from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "addon": "hello-action"}
    # return {
    #     "status": "error",
    #     "addon": "hello-action",
    #     "error_code": "MISSING_CONFIG",
    #     "error_message": "Required config key 'apiKey' was not found.",
    # }


@router.get("/demo")
def demo():
    return {"message": "Hello from hello-action backend!"}


class BackendAddon:
    """
    Minimal object to satisfy the core loader.

    It only needs:
      - id: str
      - name: str
      - router: APIRouter
    """
    def __init__(self, id: str, name: str, router: APIRouter) -> None:
        self.id = id
        self.name = name
        self.router = router


addon = BackendAddon(
    id="hello-action",
    name="Hello Action Runner",
    router=router,
)
