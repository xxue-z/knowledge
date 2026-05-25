export const errorCodes = {
  '00001': 'errors.dbConnectionFailed',
  '00002': 'errors.redisConnectionFailed',
  '00003': 'errors.milvusConnectionFailed',
  '00004': 'errors.llmServiceUnavailable',
  '00005': 'errors.keycloakUnavailable',
  
  '10001': 'errors.systemAlreadyInitialized',
  '10002': 'errors.adminPasswordTooShort',
  '10003': 'errors.configFileWriteFailed',
  '10004': 'errors.dbTableCreateFailed',
  
  '11001': 'errors.builtinAdminDisabled',
  '11002': 'errors.invalidCredentials',
  '11003': 'errors.tokenExpired',
  '11004': 'errors.insufficientPermissions',
  '11005': 'errors.keycloakAuthFailed',
  '11006': 'errors.oldPasswordIncorrect',
  '11007': 'errors.newPasswordTooShort',
  
  '99001': 'errors.validationError',
  '99002': 'errors.resourceNotFound',
  '99003': 'errors.methodNotAllowed',
  '99004': 'errors.requestExpired',
  '99005': 'errors.signatureVerificationFailed',
  '99006': 'errors.missingSignatureHeaders'
}

export function getErrorCodeKey(errorCode) {
  return errorCodes[errorCode] || 'errors.unknownError'
}
