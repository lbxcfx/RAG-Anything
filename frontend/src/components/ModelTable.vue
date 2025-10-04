<template>
  <div>
    <el-empty v-if="models.length === 0" description="暂无模型配置" />
    <el-table v-else :data="models" style="width: 100%">
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="api_type" label="API类型" width="120" />
      <el-table-column prop="model_id" label="模型ID" />
      <el-table-column label="API Key" width="150">
        <template #default="{ row }">
          <span>{{ row.api_key_masked || '****' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="默认" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_default ? 'success' : 'info'">
            {{ row.is_default ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="$emit('edit', row)">
            编辑
          </el-button>
          <el-button v-if="!row.is_default" link type="success" size="small" @click="$emit('set-default', row.id)">
            设为默认
          </el-button>
          <el-button link type="danger" size="small" @click="$emit('delete', row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  models: any[]
}>()

defineEmits<{
  edit: [model: any]
  delete: [id: number]
  'set-default': [id: number]
}>()
</script>
