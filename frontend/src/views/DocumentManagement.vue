<template>
  <div class="document-management">
    <div class="page-header">
      <h2>文档管理</h2>
      <div class="header-actions">
        <el-button icon="Back" @click="router.back()">返回</el-button>
        <el-button type="primary" icon="Upload" @click="handleUpload">上传文档</el-button>
      </div>
    </div>

    <el-card class="kb-info" v-if="knowledgeBase">
      <h3>{{ knowledgeBase.name }}</h3>
      <p>{{ knowledgeBase.description }}</p>
    </el-card>

    <el-card>
      <el-table :data="documents" v-loading="loading">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column label="状态" width="180">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="info">等待处理</el-tag>
            <el-tag v-else-if="row.status === 'parsing'" type="warning">
              <el-icon class="is-loading"><Loading /></el-icon>
              解析中
            </el-tag>
            <el-tag v-else-if="row.status === 'analyzing'" type="warning">
              <el-icon class="is-loading"><Loading /></el-icon>
              分析中
            </el-tag>
            <el-tag v-else-if="row.status === 'building_graph'" type="warning">
              <el-icon class="is-loading"><Loading /></el-icon>
              构建图谱
            </el-tag>
            <el-tag v-else-if="row.status === 'embedding'" type="warning">
              <el-icon class="is-loading"><Loading /></el-icon>
              嵌入中
            </el-tag>
            <el-tag v-else-if="row.status === 'completed'" type="success">已完成</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :status="row.status === 'failed' ? 'exception' : row.status === 'completed' ? 'success' : undefined"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleViewPipeline(row)"
              v-if="row.status !== 'pending'"
            >
              查看流程
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!documents.length" description="暂无文档，请上传" />
    </el-card>

    <el-dialog v-model="uploadVisible" title="上传文档" width="600px">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :multiple="true"
        :on-change="handleFileChange"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF, DOCX, TXT, MD 等格式，单个文件不超过 50MB
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleSubmitUpload">
          开始上传
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pipelineVisible" title="处理流程" width="800px">
      <div class="pipeline-container" v-if="selectedDoc">
        <el-steps :active="getPipelineStep(selectedDoc.status)" align-center>
          <el-step title="解析" description="提取文本和结构" />
          <el-step title="分析" description="内容理解和分类" />
          <el-step title="构建图谱" description="提取实体和关系" />
          <el-step title="向量化" description="生成嵌入向量" />
        </el-steps>

        <div class="pipeline-details" v-if="selectedDoc.pipeline_result">
          <el-tabs v-model="activeResultTab">
            <el-tab-pane label="解析结果" name="parsing" v-if="selectedDoc.pipeline_result.parsing">
              <div class="result-content">
                <pre>{{ JSON.stringify(selectedDoc.pipeline_result.parsing, null, 2) }}</pre>
              </div>
            </el-tab-pane>
            <el-tab-pane label="分析结果" name="analyzing" v-if="selectedDoc.pipeline_result.analyzing">
              <div class="result-content">
                <pre>{{ JSON.stringify(selectedDoc.pipeline_result.analyzing, null, 2) }}</pre>
              </div>
            </el-tab-pane>
            <el-tab-pane label="图谱数据" name="graph" v-if="selectedDoc.pipeline_result.graph">
              <div class="result-content">
                <h4>实体 ({{ selectedDoc.pipeline_result.graph.entities?.length || 0 }})</h4>
                <el-tag
                  v-for="entity in selectedDoc.pipeline_result.graph.entities?.slice(0, 20)"
                  :key="entity.id"
                  style="margin: 4px"
                >
                  {{ entity.name }}
                </el-tag>
                <h4 style="margin-top: 16px">关系 ({{ selectedDoc.pipeline_result.graph.relations?.length || 0 }})</h4>
                <div v-for="rel in selectedDoc.pipeline_result.graph.relations?.slice(0, 10)" :key="rel.id">
                  {{ rel.source }} → {{ rel.type }} → {{ rel.target }}
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="嵌入信息" name="embedding" v-if="selectedDoc.pipeline_result.embedding">
              <div class="result-content">
                <p>嵌入维度: {{ selectedDoc.pipeline_result.embedding.dimension }}</p>
                <p>向量数量: {{ selectedDoc.pipeline_result.embedding.count }}</p>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <el-alert
          v-if="selectedDoc.error_message"
          type="error"
          :title="selectedDoc.error_message"
          :closable="false"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeBaseApi } from '@/api/knowledge-base'
import { documentsApi } from '@/api/documents'

const route = useRoute()
const router = useRouter()

const kbId = Number(route.params.id)
const knowledgeBase = ref<any>(null)
const documents = ref<any[]>([])
const loading = ref(false)
const uploadVisible = ref(false)
const uploading = ref(false)
const fileList = ref<any[]>([])
const pipelineVisible = ref(false)
const selectedDoc = ref<any>(null)
const activeResultTab = ref('parsing')
const pollInterval = ref<any>(null)

let ws: WebSocket | null = null

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const getPipelineStep = (status: string) => {
  const steps: Record<string, number> = {
    pending: 0,
    parsing: 1,
    analyzing: 2,
    building_graph: 3,
    embedding: 4,
    completed: 4,
    failed: -1,
  }
  return steps[status] || 0
}

const loadKnowledgeBase = async () => {
  try {
    knowledgeBase.value = await knowledgeBaseApi.get(kbId)
  } catch (error) {
    console.error(error)
  }
}

const loadDocuments = async () => {
  loading.value = true
  try {
    documents.value = await documentsApi.list({ kb_id: kbId })
    // Check if any documents are still processing
    const hasProcessing = documents.value.some(doc =>
      ['parsing', 'analyzing', 'building_graph', 'embedding'].includes(doc.status)
    )
    // If there are processing documents, poll for updates
    if (hasProcessing && !pollInterval.value) {
      startPolling()
    } else if (!hasProcessing && pollInterval.value) {
      stopPolling()
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleUpload = () => {
  fileList.value = []
  uploadVisible.value = true
}

const handleFileChange = (file: any, files: any[]) => {
  fileList.value = files
}

const handleSubmitUpload = async () => {
  if (!fileList.value.length) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    for (const file of fileList.value) {
      await documentsApi.upload(kbId, file.raw)
    }
    ElMessage.success('上传成功')
    uploadVisible.value = false
    await loadDocuments()
  } catch (error) {
    console.error(error)
  } finally {
    uploading.value = false
  }
}

const handleViewPipeline = (doc: any) => {
  selectedDoc.value = doc
  pipelineVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await documentsApi.delete(id)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/v1/documents/ws/${kbId}`

  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    const docIndex = documents.value.findIndex(d => d.id === data.id)
    if (docIndex !== -1) {
      documents.value[docIndex] = { ...documents.value[docIndex], ...data }
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

const startPolling = () => {
  if (pollInterval.value) return
  // Poll every 2 seconds for progress updates
  pollInterval.value = setInterval(async () => {
    try {
      const updatedDocs = await documentsApi.list({ kb_id: kbId })
      documents.value = updatedDocs
      // Stop polling if no more processing documents
      const hasProcessing = updatedDocs.some(doc =>
        ['parsing', 'analyzing', 'building_graph', 'embedding'].includes(doc.status)
      )
      if (!hasProcessing) {
        stopPolling()
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

onMounted(() => {
  loadKnowledgeBase()
  loadDocuments()
  connectWebSocket()
})

onUnmounted(() => {
  stopPolling()
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped lang="scss">
.document-management {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      gap: 12px;
    }
  }

  .kb-info {
    margin-bottom: 20px;

    h3 {
      margin: 0 0 8px 0;
    }

    p {
      margin: 0;
      color: #666;
    }
  }

  .pipeline-container {
    .el-steps {
      margin-bottom: 32px;
    }

    .pipeline-details {
      margin-top: 24px;

      .result-content {
        max-height: 400px;
        overflow-y: auto;

        pre {
          background: #f5f7fa;
          padding: 16px;
          border-radius: 4px;
          font-size: 12px;
        }

        h4 {
          margin: 8px 0;
        }
      }
    }
  }
}
</style>
