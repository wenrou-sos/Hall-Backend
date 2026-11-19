
import env_setting

# FlashPay Credit

if env_setting.PRODUCTION_MODE ==True:
    Action_create_order = 'https://pay-openapi.flashfin.com/upay/cashier/precreate-payment'
    Action_search_order = 'https://pay-openapi.flashfin.com/upay/get-payment-result'
    if env_setting.LOCAL_SERVER == True:
        notifyUrl = 'https://34.87.72.250/flashpaynotify'
        returnUrl = 'https://34.87.72.250/flashpayreturn'
    else:
        notifyUrl = 'https://34.87.72.250/flashpaynotify'
        returnUrl = 'https://34.87.72.250/flashpayreturn'
    appKey = ''         # 正式環境用
    charset = 'UTF-8'
    signType = 'RSA2'
    version = '1.0'
else:
    Action_create_order = 'https://test-pay-openapi.flashfin.com/upay/cashier/precreate-payment'
    Action_search_order = 'https://test-pay-openapi.flashfin.com/upay/get-payment-result'
    if env_setting.LOCAL_SERVER == True:
        notifyUrl = 'https://34.87.72.250/flashpayreturn'
        returnUrl = 'https://34.87.72.250/flashpayreturn'
    else:
        notifyUrl = 'https://34.87.72.250/flashpayreturn'
        returnUrl = 'https://34.87.72.250/flashpayreturn'
    appKey = ''          # 測試用商家號
    charset = 'UTF-8'
    signType = 'RSA2'
    version = '1.0'