from pymodbus.client import ModbusSerialClient
# Modbus RTUクライアント設定
client = ModbusSerialClient(
    port="COM7",
    baudrate=9600,
    bytesize=8,
    parity='E',    # Even parity
    stopbits=1,
    timeout=1
)
# 接続開始
if not client.connect():
    print("接続失敗: COM7")
# SV（目標値）の設定
SLAVE_ID = 1       # 通信ユニットNo.（デフォルト1）
SV_ADDR  = 0x2103  # SVのレジスタアドレス
SV_VALUE = 500     # 設定温度（39℃）
# レジスタに書き込み
result = client.write_register(address=SV_ADDR, value=SV_VALUE,device_id=1)
if result.isError():
    print("書き込み失敗:", result)
else:
    print("SVを39℃に設定しました。")
client.close()
