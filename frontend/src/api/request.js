import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import i18n from '@/i18n'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.response?.data?.message

    // 根据错误消息进行特殊处理
    if (detail === '内置管理员已停用，请使用您创建的管理员账号登录' ||
        detail === 'Built-in admin is disabled, please use the admin account you created') {
      ElMessage.warning(i18n.global.t('login.builtinDisabled'))
    } else if (status === 401) {
      localStorage.removeItem('token')
      ElMessage.warning(i18n.global.t('login.sessionExpired'))
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    } else if (status === 403) {
      ElMessage.warning(detail || i18n.global.t('common.msg.noPermission'))
    } else if (status === 404) {
      ElMessage.error(detail || i18n.global.t('common.msg.notFound'))
    } else if (status === 500) {
      ElMessage.error(i18n.global.t('common.msg.serverError'))
    } else {
      ElMessage.error(detail || i18n.global.t('common.msg.requestFailed'))
    }

    return Promise.reject(error)
  }
)

export default request
