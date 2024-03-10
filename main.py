import uvicorn
from fastapi import FastAPI
from smartcard.scard import *
from smartcard.util import toHexString

COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00]

app = FastAPI()

@app.get("/")
def read_root():
    try:
        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        assert hresult == SCARD_S_SUCCESS, "ไม่พบเครื่องอ่านบัตร"
        try:
            hresult, readers = SCardListReaders(hcontext, [])
            assert hresult == SCARD_S_SUCCESS, "ไม่พบเครื่องอ่านบัตร"
            print("เครื่องอ่านบัตรที่พบ:", readers)
            assert len(readers) > 0, "ไม่พบเครื่องอ่านบัตร"
            zreader = readers[0]
            print("กำลังเชื่อมต่อเครื่องอ่านบัตรที่ชื่อ", zreader)
            try:
                hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, zreader, SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
                assert hresult == SCARD_S_SUCCESS, "กรุณาแนบบัตร"
                print("จำนวนเชื่อมต่อกับโปรโตคอลที่ใช้งานอยู่", dwActiveProtocol)
                try:
                    hresult, response = SCardTransmit(hcard, dwActiveProtocol, COMMAND)
                    assert hresult == SCARD_S_SUCCESS, "การอ่านบัตรล้มเหลว"
                    return {"status": True, "message": toHexString(response).strip()}
                finally:
                    hresult = SCardDisconnect(hcard, SCARD_UNPOWER_CARD)
                    assert hresult == SCARD_S_SUCCESS, "ตัดการเชื่อมต่อล้มเหลว"
                    print("ตัดการเชื่อมต่อแล้ว")
            except AssertionError as message:
                print(message)
                return {"status": False, "message": str(message).strip()}
        finally:
            hresult = SCardReleaseContext(hcontext)
            assert hresult == SCARD_S_SUCCESS, "ไม่พบเครื่องอ่านบัตร"
    except AssertionError as message:
        print(message)
        return {"status": False, "message": str(message).strip()}

if __name__ == "__main__":
    config = uvicorn.Config("main:app", host="0.0.0.0" , port=8000, reload=True, log_level="info")
    server = uvicorn.Server(config)
    server.run()
    