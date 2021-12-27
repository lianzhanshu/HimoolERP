<template>
  <div>
    <a-card title="供应商">
      <a-row gutter="16">
        <a-col :span="24" :md="6" :xl="5" style="max-width: 256px; margin-bottom: 12px;">
          <a-select v-model="searchForm.is_active" placeholder="状态" allowClear style="width: 100%;" @change="search">
            <a-select-option :value="true">激活</a-select-option>
            <a-select-option :value="false">冻结</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="24" :md="6" :xl="4" style="max-width: 256px; margin-bottom: 12px;">
          <a-input-search v-model="searchForm.search" placeholder="编号, 名称, 备注" allowClear @search="search" />
        </a-col>
        <a-col :span="24" :md="6" :xl="8" style="margin-bottom: 12px;">
          <a-button-group>
            <a-button icon="file-excel" @click="downloadTemplate">模板下载</a-button>
            <a-upload name="file" :showUploadList="false" :customRequest="importExcel">
              <a-button icon="upload">导入</a-button>
            </a-upload>
            <a-button icon="download" @click="exportExcel">导出</a-button>
          </a-button-group>
        </a-col>

        <div style="margin-bottom: 12px; float: right;">
          <a-button type="primary" icon="plus" style="margin: 0 8px;" @click="openFormModal(form)">新增供应商</a-button>
        </div>
      </a-row>

      <a-row style="margin-top: 12px;">
        <a-table size="small" :columns="columns" :dataSource="items" rowKey="id" :loading="loading" :pagination="pagination"
          @change="tableChange">
          <div slot="is_active" slot-scope="value">
            <a-tag :color="value ? 'green' : 'red'">{{value ? '激活' : '冻结'}}</a-tag>
          </div>
          <div slot="action" slot-scope="value, item">
            <a-button-group>
              <a-button icon="edit" size="small" @click="openFormModal(item)">编辑</a-button>
              <a-popconfirm title="确定删除吗" @confirm="destroy(item.id)">
                <a-button type="danger" icon="delete" size="small">删除</a-button>
              </a-popconfirm>
            </a-button-group>
          </div>
        </a-table>
      </a-row>
    </a-card>
    <form-modal v-model="visible" :form="targetItem" :suppliersClassificationOptions="suppliersClassificationOptions" @create="create" @update="update" />
    <a-modal v-model="importLoading" :footer="null" :maskClosable="false" :closable="false">
      <div>
        <a-spin style="margin-right: 12px;" />正在导入中, 请等待...
      </div>
    </a-modal>
  </div>
</template>

<script>
  import { exportExcel } from '@/utils/excel'
  import { supplierExport } from '@/api/export'
  import { supplierTemplate, supplierImport } from '@/api/import'
  import { supplierList, supplierDestroy } from '@/api/basicData'
  import { getSupplierNumber } from '@/api/data'
  import { supplierClassification }  from '@/api/option'

  export default {
    name: 'Warehouse',
    components: {
      FormModal: () => import('./FormModal.vue'),
    },
    data() {
      return {
        columns: [
          {
            title: '序号',
            dataIndex: 'index',
            key: 'index',
            customRender: (value, item, index) => {
              return index + 1
            },
          },
          {
            title: '供应商名称',
            dataIndex: 'name',
            sorter: true,
          },
          {
            title: '供应商编号',
            dataIndex: 'number',
          },
          {
            title: '联系人',
            dataIndex: 'contact',
          },
          {
            title: '手机号',
            dataIndex: 'phone',
          },
          {
            title: '排序',
            dataIndex: 'order',
            sorter: true,
          },
          {
            title: '状态',
            dataIndex: 'is_active',
            scopedSlots: { customRender: 'is_active' }
          },
          {
            title: '操作',
            dataIndex: 'action',
            scopedSlots: { customRender: 'action' },
            width: '156px'
          },
        ],
        searchForm: { search: '', page: 1 },
        pagination: { current: 1, total: 0, pageSize: 15 },
        loading: false,
        items: [],
        suppliersClassificationOptions: [],
        visible: false,
        targetItem: {},
        form: { is_active: true },
        importLoading: false,
      };
    },
    computed: {
    },
    methods: {
      initialize() {
        this.list();
      },
      list() {
        this.loading = true;
        supplierList(this.searchForm).then(data => {
          this.pagination.total = data.count;
          this.items = data.results;
        }).finally(() => {
          this.loading = false;
        });
      },
      create(item) {
        this.items.splice(0, 0, item);
      },
      update(item) {
        this.items.splice(this.items.findIndex(i => i.id == item.id), 1, item);
      },
      search() {
        this.searchForm.page = 1;
        this.pagination.current = 1;
        this.list();
      },
      openFormModal(item) {
        if (!item.id) {
          getSupplierNumber().then(data => {
            this.targetItem = { ...item, ...{ number: data.number } };
          })
        } else {
          this.targetItem = { ...item };
        }
        supplierClassification({ page_size: 999999 }).then(data => {
          this.suppliersClassificationOptions = data.results;
        });
        this.visible = true;
      },
      destroy(id) {
        supplierDestroy({ id }).then(() => {
          this.items.splice(this.items.findIndex(item => item.id == id), 1);
          this.$message.success('删除成功');
        });
      },
      exportExcel() {
        supplierExport(this.searchForm).then(resp => {
          exportExcel(resp.data, '供应商列表');
        }).catch(err => {
          this.$message.error(err.response.data.error);
        });
      },
      downloadTemplate () {
        supplierTemplate().then(resp => {
          exportExcel(resp.data, '供应商导入模板');
        }).catch(err => {
          this.$message.error(err.response.data.error);
        });
      },
      importExcel(item) {
        let data = new FormData();
        data.append('file', item.file);
        this.importLoading = true;
        setTimeout(() => {
          supplierImport(data)
            .then(() => {
              this.$message.success('导入成功');
              this.list();
            })
            .catch(err => {
              this.$message.error(err.response.data.detail);
            })
            .finally(() => {
              this.importLoading = false;
            });
        }, 1000);
      },
    },
    mounted() {
      this.initialize();
    },
  }
</script>