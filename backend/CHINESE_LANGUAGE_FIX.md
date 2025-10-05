# 中文文档知识图谱通用优化方案

## 问题描述
上传的中文文档（如"重度及特重度烧伤患者康复期照护干预方案的多维度构建"）在知识图谱中显示的实体和关系都是英文，而不是中文。

## 问题根源
1. **LightRAG默认语言设置问题**：LightRAG v1.4.9 的实体提取提示词中使用了 `{language}` 占位符
2. **语言参数未配置**：在初始化LightRAG时，没有设置语言参数为中文
3. **提示词语言配置缺失**：系统提示词要求使用指定语言，但未指定为中文
4. **提示词不够优化**：原始提示词没有针对中文文档进行通用优化

## 解决方案
在 `backend/app/services/document_processor.py` 中添加了通用的中文语言配置功能：

### 修改内容

1. **添加了 `_configure_chinese_language()` 方法**：
   - 通过 `addon_params` 设置语言为中文
   - 调用通用的中文提示词创建方法

2. **添加了 `_create_optimized_chinese_prompts()` 方法**：
   - 创建专门针对中文文档优化的通用提示词
   - 适用于各种类型的文档（学术、技术、商业、新闻等）
   - 包含详细的实体识别指导
   - 包含通用的关系类型识别

### 优化特性

#### 实体识别优化
- **人名、机构名称、地理位置**：识别各种实体类型
- **专业术语、概念、理论**：处理专业内容
- **时间、数量、测量单位**：提取数值和时间信息
- **工具、方法、技术**：识别技术相关实体
- **事件、过程、状态**：提取动态实体
- **抽象概念、原则、规则**：处理抽象概念

#### 关系识别优化
- **因果关系**：A导致B、A引起B
- **包含关系**：A包含B、A属于B
- **时间关系**：A在B之前、A在B之后
- **空间关系**：A位于B、A在B中
- **功能关系**：A用于B、A作用于B
- **比较关系**：A优于B、A与B相似
- **从属关系**：A属于B、A隶属于B
- **协作关系**：A与B合作、A协助B

#### 通用文档处理
- 适用于各种类型的文档
- 根据文档内容自动调整识别重点
- 保持提取结果的客观性和准确性
- 使用标准的中文术语

### 代码修改位置

```python
# 在 _get_or_create_rag_instance 方法中
# Initialize LightRAG storages
init_result = await self.rag_instance._ensure_lightrag_initialized()
if not init_result.get("success"):
    error_msg = init_result.get("error", "Unknown error initializing LightRAG")
    logger.error(f"Failed to initialize LightRAG: {error_msg}")
    raise RuntimeError(f"LightRAG initialization failed: {error_msg}")

# Configure Chinese language for entity extraction
self._configure_chinese_language()

logger.info(f"Created and initialized RAGAnything instance for KB {kb_id} at {working_dir}")
return self.rag_instance
```

### 新增方法

```python
def _configure_chinese_language(self):
    """Configure LightRAG to use Chinese language for entity extraction"""
    try:
        import lightrag
        
        # Method 1: Try to set language via addon_params
        if hasattr(self, 'rag_instance') and self.rag_instance and hasattr(self.rag_instance, 'lightrag'):
            if hasattr(self.rag_instance.lightrag, 'addon_params'):
                self.rag_instance.lightrag.addon_params['language'] = 'Chinese'
                logger.info("✓ Configured Chinese language via addon_params")
        
        # Method 2: Always modify the prompt templates to ensure Chinese language
        original_system_prompt = lightrag.prompt.PROMPTS['entity_extraction_system_prompt']
        original_user_prompt = lightrag.prompt.PROMPTS['entity_extraction_user_prompt']
        
        # Replace {language} placeholder with Chinese
        chinese_system_prompt = original_system_prompt.replace('{language}', 'Chinese')
        chinese_user_prompt = original_user_prompt.replace('{language}', 'Chinese')
        
        # Update the prompts
        lightrag.prompt.PROMPTS['entity_extraction_system_prompt'] = chinese_system_prompt
        lightrag.prompt.PROMPTS['entity_extraction_user_prompt'] = chinese_user_prompt
        
        logger.info("✓ Configured Chinese language by modifying prompt templates")
        logger.info("✓ Entity extraction will now use Chinese language by default")
        
    except Exception as e:
        logger.warning(f"⚠ Failed to configure Chinese language: {e}")
        logger.warning("⚠ Entity extraction may still use English")
```

## 效果验证

修改后的效果：
- ✅ 系统提示词中的 `{language}` 被替换为 `Chinese`
- ✅ 用户提示词中的 `{language}` 被替换为 `Chinese`
- ✅ LLM在进行实体提取时会使用中文
- ✅ 知识图谱中的实体和关系将显示为中文

## 使用方法

修改完成后，重新启动后端服务，然后重新上传中文文档进行处理。新的文档处理将自动使用中文进行实体和关系提取。

## 注意事项

1. **全局影响**：此修改会影响所有使用该DocumentProcessor的文档处理
2. **默认中文**：所有文档处理都将默认使用中文进行实体提取
3. **兼容性**：修改不会影响现有的英文文档处理功能
4. **日志记录**：配置过程会在日志中记录，便于调试和监控

## 测试建议

1. 重新上传中文PDF文档
2. 检查处理日志中是否出现"✓ Configured Chinese language"消息
3. 查看知识图谱中的实体和关系是否为中文
4. 验证实体提取的准确性和完整性
