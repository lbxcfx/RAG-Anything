<template>
  <div class="model-config">
    <div class="page-header">
      <h2>模型配置</h2>
      <el-button type="primary" icon="Plus" @click="handleCreate">添加模型</el-button>
    </div>

    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="LLM模型" name="llm">
          <ModelTable :models="llmModels" @edit="handleEdit" @delete="handleDelete" @set-default="handleSetDefault" />
        </el-tab-pane>
        <el-tab-pane label="VLM模型" name="vlm">
          <ModelTable :models="vlmModels" @edit="handleEdit" @delete="handleDelete" @set-default="handleSetDefault" />
        </el-tab-pane>
        <el-tab-pane label="Embedding模型" name="embedding">
          <ModelTable :models="embeddingModels" @edit="handleEdit" @delete="handleDelete" @set-default="handleSetDefault" />
        </el-tab-pane>
        <el-tab-pane label="Rerank模型" name="rerank">
          <ModelTable :models="rerankModels" @edit="handleEdit" @delete="handleDelete" @set-default="handleSetDefault" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型类型" prop="model_type">
          <el-select v-model="form.model_type" placeholder="请选择模型类型" style="width: 100%">
            <el-option label="LLM" value="llm" />
            <el-option label="VLM" value="vlm" />
            <el-option label="Embedding" value="embedding" />
            <el-option label="Rerank" value="rerank" />
          </el-select>
        </el-form-item>
        <el-form-item label="API类型" prop="provider">
          <el-select v-model="form.provider" placeholder="请选择API类型" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="Gemini" value="gemini" />
            <el-option label="阿里云DashScope" value="alibaba-dashscope" />
            <el-option label="本地模型" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型ID" prop="model_name">
          <el-input v-model="form.model_name" placeholder="例如: gpt-4, claude-3-opus, qwen-max" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="请输入API Key" />
        </el-form-item>
        <el-form-item label="Base URL" prop="api_base_url">
          <el-input v-model="form.api_base_url" placeholder="可选，默认使用官方API地址" />
        </el-form-item>
        <el-form-item label="设为默认" prop="is_default">
          <el-switch v-model="form.is_default" />
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { modelsApi } from '@/api/models'
import ModelTable from '@/components/ModelTable.vue'

const activeTab = ref('llm')
const dialogVisible = ref(false)
const dialogTitle = ref('添加模型')
const loading = ref(false)
const formRef = ref<FormInstance>()

const models = ref<any[]>([])

const llmModels = computed(() => models.value.filter((m) => m.model_type === 'llm'))
const vlmModels = computed(() => models.value.filter((m) => m.model_type === 'vlm'))
const embeddingModels = computed(() => models.value.filter((m) => m.model_type === 'embedding'))
const rerankModels = computed(() => models.value.filter((m) => m.model_type === 'rerank'))

const form = ref({
  id: undefined as number | undefined,
  name: '',
  model_type: '',
  provider: '',
  model_name: '',
  api_key: '',
  api_base_url: '',
  is_default: false,
})

const rules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  model_type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  provider: [{ required: true, message: '请选择API类型', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }],
}

const loadModels = async () => {
  try {
    models.value = await modelsApi.list()
  } catch (error) {
    console.error(error)
  }
}

const handleCreate = () => {
  dialogTitle.value = '添加模型'
  form.value = {
    id: undefined,
    name: '',
    model_type: activeTab.value,
    provider: '',
    model_name: '',
    api_key: '',
    api_base_url: '',
    is_default: false,
  }
  dialogVisible.value = true
}

const handleEdit = (model: any) => {
  dialogTitle.value = '编辑模型'
  form.value = { ...model }
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此模型吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await modelsApi.delete(id)
    ElMessage.success('删除成功')
    await loadModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleSetDefault = async (id: number) => {
  try {
    await modelsApi.setDefault(id)
    ElMessage.success('设置成功')
    await loadModels()
  } catch (error) {
    console.error(error)
  }
}

const handleSubmit = async () => {
  await formRef.value?.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (form.value.id) {
          await modelsApi.update(form.value.id, form.value)
          ElMessage.success('更新成功')
        } else {
          await modelsApi.create(form.value)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await loadModels()
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
  loadModels()
})
</script>

<style scoped lang="scss">
.model-config {
  .page-header {
    margin-bottom: 20px;
  }
}
</style>
