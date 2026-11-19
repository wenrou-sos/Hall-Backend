
import env_setting

# ECPay Credit

if env_setting.PRODUCTION_MODE ==True:
    Action = 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'
    if env_setting.LOCAL_SERVER == True:
        ReturnURL = 'https://jinsong.io/ecpay/serverorderresult'
        ClientBackURL = 'https://dev.jinsong.io/ecpay/clientorderresult'
    else:
        ReturnURL = 'https://jinsong.io/ecpay/serverorderresult'
        ClientBackURL = 'https://jinsong.io/ecpay/clientorderresult'
    MerchantID = '3187789'
    HashKey = 'lqSe83oAzUMwODU6'
    HashIV = 'sskn3ZFYYm5oXmad'
else:
    Action = 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'
    if env_setting.LOCAL_SERVER == True:
        ReturnURL = 'https://inner.jinsong.io/ecpay/serverorderresult'
        ClientBackURL = 'https://dev.jinsong.io/ecpay/clientorderresult'
    else:
        ReturnURL = 'https://inner.jinsong.io/ecpay/serverorderresult'
        ClientBackURL = 'https://inner.jinsong.io/ecpay/clientorderresult'
    MerchantID = '2000132'          # 測試用商家號
    HashKey = '5294y06JbISpM5x9'
    HashIV = 'v77hoKGq4kWxNNIS'