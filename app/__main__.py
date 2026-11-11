import os

import uvicorn

from app.main import create_app


def main() -> None:
    certificado = os.environ.get("SSL_CERTFILE")
    chave = os.environ.get("SSL_KEYFILE")
    if not certificado or not chave:
        raise SystemExit("Defina SSL_CERTFILE e SSL_KEYFILE para iniciar em HTTPS/WSS.")

    uvicorn.run(
        create_app(),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORTA", "8443")),
        ssl_certfile=certificado,
        ssl_keyfile=chave,
        ws="websockets-sansio",
    )


if __name__ == "__main__":
    main()
