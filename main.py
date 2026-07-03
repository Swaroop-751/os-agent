from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml
from app.agent_core import plan_actions, apply_actions
from app.policy import is_valid_role

import os
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
with open(config_path) as f:
    CFG = yaml.safe_load(f)

app = FastAPI(title="GenAI Linux Agent")

class PlanRequest(BaseModel):
    user: str
    role: str = "operator"
    message: str

class ApplyRequest(BaseModel):
    user: str

@app.post("/plan")
def plan(req: PlanRequest):
    if not is_valid_role(req.role):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role {req.role!r}. Must be one of viewer, operator, admin."
        )
    try:
        plan, explanation, requires_approval = plan_actions(req.user, req.role, req.message)
        return {"plan": plan, "explanation": explanation, "requires_approval": requires_approval}
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apply")
def apply(req: ApplyRequest):
    if not CFG["agent"].get("auto_apply", False):
        raise HTTPException(status_code=403, detail="Auto-apply disabled")
    try:
        return apply_actions(req.user)
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apply_pending")
def apply_pending(req: ApplyRequest):
    try:
        return apply_actions(req.user)
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz")
def healthz():
    return {"ok": True}
