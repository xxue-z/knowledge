import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import i18n from '@/i18n'
import { signRequest } from '@/utils/sign'
import { getErrorCodeKey } from '@/utils/errorCodes'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

const SIGNATURE_SECRET = import.meta.env.VITE_SIGNATURE_SECRET || 'knowledge-platform-default-signature-secret-change-in-production'

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    if (SIGNATURE_SECRET) {
      signRequest(config, SIGNATURE_SECRET)
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
    const errorCode = error.response?.data?.error_code
    const detail = error.response?.data?.detail || error.response?.data?.message

    if (errorCode) {
      const errorKey = getErrorCodeKey(errorCode)
      const errorMessage = i18n.global.t(errorKey)
      
      if (errorCode === '11001') {
        ElMessage.warning(errorMessage)
      } else if (errorCode === '11003') {
        localStorage.removeItem('token')
        ElMessage.warning(errorMessage)
        setTimeout(() => {
          window.location.href = '/login'
        }, 1500)
      } else if (status === 403) {
        ElMessage.warning(errorMessage)
      } else if (status === 404) {
        ElMessage.error(errorMessage)
      } else {
        ElMessage.error(errorMessage)
      }
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
