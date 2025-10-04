<template>
  <div class="knowledge-base">
    <div class="page-header">
      <h2>知识库管理</h2>
      <el-button type="primary" icon="Plus" @click="handleCreate">创建知识库</el-button>
    </div>

    <el-row :gutter="20">
      <el-col v-for="kb in knowledgeBases" :key="kb.id" :span="8">
        <el-card class="kb-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="kb-title">
                <el-icon><FolderOpened /></el-icon>
                <span>{{ kb.name }}</span>
              </div>
              <el-dropdown @command="(cmd) => handleCommand(cmd, kb)">
                <el-icon class="more-icon"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="chat">
                      <el-icon><ChatDotRound /></el-icon>
                      对话
                    </el-dropdown-item>
                    <el-dropdown-item command="documents">
                      <el-icon><Document /></el-icon>
                      文档管理
                    </el-dropdown-item>
                    <el-dropdown-item command="graph">
                      <el-icon><Share /></el-icon>
                      知识图谱
                    </el-dropdown-item>
                    <el-dropdown-item command="edit">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          <div class="kb-content">
            <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
            <div class="kb-stats">
              <div class="stat-item">
                <el-icon><Document /></el-icon>
                <span>{{ kb.document_count }} 文档</span>
              </div>
              <div class="stat-item">
                <el-icon><ChatDotRound /></el-icon>
                <span>{{ kb.chat_count || 0 }} 对话</span>
              </div>
            </div>
            <div class="kb-config">
              <el-tag size="small">{{ getParserName(kb.parser_config?.type) }}</el-tag>
              <el-tag v-if="kb.parser_config?.enable_ocr" size="small" type="success">OCR</el-tag>
              <el-tag v-if="kb.parser_config?.enable_table" size="small" type="warning">表格</el-tag>
            </div>
          </div>
          <template #footer>
            <el-button text @click="router.push(`/knowledge-bases/${kb.id}/chat`)">
              <el-icon><ChatDotRound /></el-icon>
              开始对话
            </el-button>
            <el-button text @click="router.push(`/knowledge-bases/${kb.id}/documents`)">
              <el-icon><Document /></el-icon>
              管理文档
            </el-button>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!knowledgeBases.length" description="暂无知识库，请创建一个吧" />

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
          />
        </el-form-item>
        <el-form-item label="解析器类型" prop="parser_type">
          <el-select v-model="form.parser_type" placeholder="请选择解析器类型" style="width: 100%">
            <el-option label="LlamaParse" value="llama_parse" />
            <el-option label="UnstructuredIO" value="unstructured_io" />
            <el-option label="Marker" value="marker" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用OCR" prop="enable_ocr">
          <el-switch v-model="form.enable_ocr" />
        </el-form-item>
        <el-form-item label="启用表格识别" prop="enable_table">
          <el-switch v-model="form.enable_table" />
        </el-form-item>
        <el-form-item label="启用公式识别" prop="enable_equation">
          <el-switch v-model="form.enable_equation" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { knowledgeBaseApi } from '@/api/knowledge-base'

const router = useRouter()

const dialogVisible = ref(false)
const dialogTitle = ref('创建知识库')
const loading = ref(false)
const formRef = ref<FormInstance>()

const knowledgeBases = ref<any[]>([])

const form = ref({
  id: undefined as number | undefined,
  name: '',
  description: '',
  parser_type: 'llama_parse',
  enable_ocr: false,
  enable_table: false,
  enable_equation: false,
})

const rules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  parser_type: [{ required: true, message: '请选择解析器类型', trigger: 'change' }],
}

const getParserName = (type: string) => {
  const names: Record<string, string> = {
    llama_parse: 'LlamaParse',
    unstructured_io: 'UnstructuredIO',
    marker: 'Marker',
  }
  return names[type] || type
}

const loadKnowledgeBases = async () => {
  try {
    knowledgeBases.value = await knowledgeBaseApi.list()
  } catch (error) {
    console.error(error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '创建知识库'
  form.value = {
    id: undefined,
    name: '',
    description: '',
    parser_type: 'llama_parse',
    enable_ocr: false,
    enable_table: false,
    enable_equation: false,
  }
  dialogVisible.value = true
}

const handleCommand = async (command: string, kb: any) => {
  switch (command) {
    case 'chat':
      router.push(`/knowledge-bases/${kb.id}/chat`)
      break
    case 'documents':
      router.push(`/knowledge-bases/${kb.id}/documents`)
      break
    case 'graph':
      router.push(`/knowledge-bases/${kb.id}/graph`)
      break
    case 'edit':
      dialogTitle.value = '编辑知识库'
      form.value = {
        id: kb.id,
        name: kb.name,
        description: kb.description,
        parser_type: kb.parser_config?.type || 'llama_parse',
        enable_ocr: kb.parser_config?.enable_ocr || false,
        enable_table: kb.parser_config?.enable_table || false,
        enable_equation: kb.parser_config?.enable_equation || false,
      }
      dialogVisible.value = true
      break
    case 'delete':
      await handleDelete(kb.id)
      break
  }
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此知识库吗？删除后无法恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await knowledgeBaseApi.delete(id)
    ElMessage.success('删除成功')
    await loadKnowledgeBases()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleSubmit = async () => {
  await formRef.value?.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const data = {
          name: form.value.name,
          description: form.value.description,
          parser_config: {
            type: form.value.parser_type,
            enable_ocr: form.value.enable_ocr,
            enable_table: form.value.enable_table,
            enable_equation: form.value.enable_equation,
          },
        }
        if (form.value.id) {
          await knowledgeBaseApi.update(form.value.id, data)
          ElMessage.success('更新成功')
        } else {
          await knowledgeBaseApi.create(data)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadKnowledgeBases()
      } catch (error) {
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped lang="scss">
.knowledge-base {
  .kb-card {
    margin-bottom: 20px;
    transition: transform 0.3s;

    &:hover {
      transform: translateY(-4px);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .kb-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
      }

      .more-icon {
        cursor: pointer;
        font-size: 18px;

        &:hover {
          color: #409eff;
        }
      }
    }

    .kb-content {
      .kb-desc {
        color: #666;
        margin-bottom: 16px;
        min-height: 48px;
      }

      .kb-stats {
        display: flex;
        gap: 24px;
        margin-bottom: 12px;

        .stat-item {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #999;
          font-size: 14px;
        }
      }

      .kb-config {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }
  }
}
</style>
