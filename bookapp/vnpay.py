import hashlib
import hmac
import urllib.parse
from datetime import datetime


class VNPay:
    def __init__(self):
        self.vnp_TmnCode = "FIMMIYKA"
        self.vnp_HashSecret = "5PQXBYWDWRXS7NHGP1XG46LW7UNW48Q0"
        self.vnp_Url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
        self.vnp_ReturnUrl = "http://localhost:5000/payment_return"

    def get_payment_url(self, order_id, total_amount, order_desc):
        vnp_Params = {}
        vnp_Params['vnp_Version'] = '2.1.0'
        vnp_Params['vnp_Command'] = 'pay'
        vnp_Params['vnp_TmnCode'] = self.vnp_TmnCode
        vnp_Params['vnp_Amount'] = int(float(total_amount) * 100)
        vnp_Params['vnp_CurrCode'] = 'VND'
        vnp_Params['vnp_TxnRef'] = str(order_id)
        vnp_Params['vnp_OrderInfo'] = order_desc
        vnp_Params['vnp_OrderType'] = 'billpayment'
        vnp_Params['vnp_Locale'] = 'vn'
        vnp_Params['vnp_ReturnUrl'] = self.vnp_ReturnUrl
        vnp_Params['vnp_IpAddr'] = '127.0.0.1'
        vnp_Params['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')

        # Sắp xếp tham số trước khi tạo chuỗi hash
        input_data = sorted(vnp_Params.items())

        # Tạo chuỗi hash data
        query_string = ''
        seq = 0
        for key, val in input_data:
            if seq == 1:
                query_string = query_string + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                query_string = key + '=' + urllib.parse.quote_plus(str(val))

        # Tạo secure hash
        vnp_SecureHash = hmac.new(
            bytes(self.vnp_HashSecret, 'utf-8'),
            bytes(query_string, 'utf-8'),
            hashlib.sha512
        ).hexdigest()

        # Thêm vnp_SecureHash vào cuối URL
        return self.vnp_Url + "?" + query_string + '&vnp_SecureHash=' + vnp_SecureHash

    def verify_response(self, response_data):
        if not response_data.get('vnp_SecureHash'):
            return False

        # Lấy secure hash từ response
        secure_hash = response_data['vnp_SecureHash']

        # Xóa các trường không cần thiết
        if 'vnp_SecureHash' in response_data:
            response_data.pop('vnp_SecureHash')
        if 'vnp_SecureHashType' in response_data:
            response_data.pop('vnp_SecureHashType')

        # Sắp xếp các tham số
        input_data = sorted(response_data.items())

        # Tạo chuỗi hash
        query_string = ''
        seq = 0
        for key, val in input_data:
            if seq == 1:
                query_string = query_string + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                query_string = key + '=' + urllib.parse.quote_plus(str(val))

        # Tạo secure hash mới
        vnp_SecureHash = hmac.new(
            bytes(self.vnp_HashSecret, 'utf-8'),
            bytes(query_string, 'utf-8'),
            hashlib.sha512
        ).hexdigest()

        return vnp_SecureHash == secure_hash
