import uvicorn
from fastapi import FastAPI
from smartcard.scard import *
from smartcard.util import toHexString
import datetime
COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00]

app = FastAPI()

@app.get("/")
def read_root():
    try:
        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        assert hresult == SCARD_S_SUCCESS, "Failed to establish context: " + SCardGetErrorMessage(hresult)
        try:
            hresult, readers = SCardListReaders(hcontext, [])
            assert hresult == SCARD_S_SUCCESS, "Failed to list readers: " + SCardGetErrorMessage(hresult)
            print("PCSC Readers:", readers)
            assert len(readers) > 0, "Cannot find a smart card reader."
            zreader = readers[0]
            print("Trying to Control reader:", zreader)
            try:
                hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, zreader, SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
                assert hresult == SCARD_S_SUCCESS, "Unable to connect: " + SCardGetErrorMessage(hresult)
                print("Connected with active protocol", dwActiveProtocol)
                try:
                    hresult, response = SCardTransmit(hcard, dwActiveProtocol, COMMAND)
                    assert hresult == SCARD_S_SUCCESS, "Failed to transmit: " + SCardGetErrorMessage(hresult)
                    return {"status": True, "message": toHexString(response).strip()}
                finally:
                    hresult = SCardDisconnect(hcard, SCARD_UNPOWER_CARD)
                    assert hresult == SCARD_S_SUCCESS, "Failed to disconnect: " + SCardGetErrorMessage(hresult)
                    print("Disconnected")
            except AssertionError as message:
                print(message)
                return {"status": False, "message": str(message).strip()}
        finally:
            hresult = SCardReleaseContext(hcontext)
            assert hresult == SCARD_S_SUCCESS, "Failed to release context: " + SCardGetErrorMessage(hresult)
    except AssertionError as message:
        print(message)
        return {"status": False, "message": str(message).strip()}

if __name__ == "__main__":
    config = uvicorn.Config("main:app", host="0.0.0.0" , port=8000, reload=True, log_level="info")
    server = uvicorn.Server(config)
    server.run()
    