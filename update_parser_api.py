"""
Script to update the _call_mineru_api method in parser.py with the corrected implementation
"""

import re

# Read the parser.py file
with open("raganything/parser.py", "r", encoding="utf-8") as f:
    content = f.read()

# The new implementation
new_implementation = '''    @staticmethod
    async def _call_mineru_api(
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        api_url: str,
        api_key: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Call MinerU cloud API service for document parsing (mineru.net)

        Uses the batch processing API:
        1. Request upload URL
        2. Upload file via PUT
        3. Poll for extraction results
        4. Download and extract ZIP file

        Args:
            input_path: Path to input file
            output_dir: Output directory path
            api_url: MinerU API base URL (e.g., https://mineru.net/api/v4/extract/task)
            api_key: API key for authentication (required for cloud service)
            method: Parsing method (auto, txt, ocr)
            lang: Document language for OCR optimization
            **kwargs: Additional parameters (formula, table, etc.)
        """
        import aiohttp
        import asyncio
        from pathlib import Path as PathlibPath
        import zipfile
        import io

        input_path = PathlibPath(input_path)
        output_dir = PathlibPath(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not api_key:
            raise ValueError("api_key is required for MinerU cloud API")

        # Extract base URL if full endpoint is provided
        if "/extract/task" in api_url:
            base_url = api_url.rsplit("/extract/task", 1)[0]
        else:
            base_url = api_url

        try:
            async with aiohttp.ClientSession() as session:
                logging.info(f"Calling MinerU Cloud API for {input_path.name}")

                # Step 1: Request upload URL
                batch_url = f"{base_url}/file-urls/batch"

                files_data = [{
                    "name": input_path.name,
                    "is_ocr": method == "ocr" or method == "auto",
                    "data_id": input_path.stem,
                    "language": lang or "ch",
                }]

                batch_request = {
                    "enable_formula": kwargs.get("formula", True),
                    "language": lang or "ch",
                    "files": files_data
                }

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

                logging.info(f"Step 1: Requesting upload URL...")
                async with session.post(
                    batch_url,
                    headers=headers,
                    json=batch_request,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as batch_response:
                    if batch_response.status != 200:
                        error_text = await batch_response.text()
                        raise RuntimeError(
                            f"Batch request failed with status {batch_response.status}: {error_text}"
                        )

                    batch_result = await batch_response.json()

                    if batch_result.get("code") != 0:
                        raise RuntimeError(f"API returned error: {batch_result.get('msg')}")

                    batch_data = batch_result.get("data", {})
                    batch_id = batch_data.get("batch_id")
                    file_urls = batch_data.get("file_urls", [])

                    if not batch_id or not file_urls:
                        raise RuntimeError("No batch_id or file_urls in response")

                    upload_url = file_urls[0]
                    logging.info(f"Got batch ID: {batch_id}")

                # Step 2: Upload file using PUT
                logging.info(f"Step 2: Uploading file ({input_path.stat().st_size:,} bytes)...")

                file_content = input_path.read_bytes()

                async with session.put(
                    upload_url,
                    data=file_content,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as upload_response:
                    if upload_response.status not in [200, 201, 204]:
                        error_text = await upload_response.text()
                        raise RuntimeError(
                            f"Upload failed with status {upload_response.status}: {error_text}"
                        )

                logging.info(f"File uploaded successfully")

                # Step 3: Poll for batch results
                logging.info(f"Step 3: Waiting for extraction completion...")
                results_url = f"{base_url}/extract-results/batch/{batch_id}"
                max_attempts = 120  # 10 minutes
                attempt = 0

                while attempt < max_attempts:
                    await asyncio.sleep(5)
                    attempt += 1

                    async with session.get(
                        results_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as results_response:
                        if results_response.status != 200:
                            logging.warning(f"Results check failed: {results_response.status}")
                            continue

                        results_data = await results_response.json()

                        if results_data.get("code") == 0:
                            # Results available
                            data = results_data.get("data", {})
                            extract_results = data.get("extract_result", [])

                            # Get the first result's full_zip_url
                            result_url = None
                            if extract_results and len(extract_results) > 0:
                                first_result = extract_results[0]
                                if first_result.get("state") == "done":
                                    result_url = first_result.get("full_zip_url")

                            if result_url:
                                logging.info(f"Step 4: Downloading results...")

                                # Download ZIP file
                                async with session.get(result_url) as zip_response:
                                    if zip_response.status == 200:
                                        zip_content = await zip_response.read()
                                        logging.info(f"Downloaded ZIP file ({len(zip_content):,} bytes)")

                                        # Extract ZIP file
                                        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                                            zf.extractall(output_dir)
                                            logging.info(f"Extracted {len(zf.namelist())} files")

                                        # Find and read the markdown file
                                        md_files = list(output_dir.glob("**/full.md"))
                                        if not md_files:
                                            md_files = list(output_dir.glob("**/*.md"))

                                        if md_files:
                                            md_file = md_files[0]
                                            content = md_file.read_text(encoding="utf-8")

                                            # Copy to standard location
                                            output_md = output_dir / f"{input_path.stem}.md"
                                            output_md.write_text(content, encoding="utf-8")

                                            # Create content_list.json for compatibility
                                            content_list = [{
                                                "type": "text",
                                                "text": content,
                                                "page_idx": 0
                                            }]
                                            json_file = output_dir / f"{input_path.stem}_content_list.json"
                                            with open(json_file, "w", encoding="utf-8") as f:
                                                json.dump(content_list, f, ensure_ascii=False, indent=2)

                                            logging.info(f"Successfully processed {input_path.name}")
                                            return  # Success
                                        else:
                                            raise RuntimeError("No markdown file found in ZIP")
                                    else:
                                        raise RuntimeError(f"Failed to download ZIP: {zip_response.status}")

                        elif results_data.get("code") == 1:
                            # Still processing
                            if attempt % 6 == 0:  # Log every 30 seconds
                                logging.info(f"Processing... ({attempt * 5}s elapsed)")
                            continue
                        else:
                            error_msg = results_data.get("msg", "Unknown error")
                            raise RuntimeError(f"API error: {error_msg}")

                # Timeout
                raise RuntimeError(f"Polling timeout after {max_attempts * 5} seconds")

        except aiohttp.ClientError as e:
            logging.error(f"MinerU API network error: {e}")
            raise RuntimeError(f"Failed to connect to MinerU API: {e}")
        except Exception as e:
            logging.error(f"MinerU API error: {e}")
            raise'''

# Find and replace the method
pattern = r'    @staticmethod\s+async def _call_mineru_api\(.*?\n(?:.*?\n)*?.*?raise'

# Find the method
match = re.search(pattern, content, re.DOTALL)

if match:
    # Find the end of the method (next method definition or class end)
    start_pos = match.start()

    # Find the end: look for next @staticmethod or next method definition at same indentation
    remaining = content[start_pos:]

    # Find the next method or end of class
    next_method = re.search(r'\n    @staticmethod\n|^\n    def |^class ', remaining[100:], re.MULTILINE)

    if next_method:
        end_pos = start_pos + 100 + next_method.start()
    else:
        end_pos = len(content)

    # Replace the old method with the new one
    new_content = content[:start_pos] + new_implementation + '\n' + content[end_pos:]

    # Write the updated content
    with open("raganything/parser.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ Successfully updated _call_mineru_api method in parser.py!")
else:
    print("❌ Could not find _call_mineru_api method in parser.py")
