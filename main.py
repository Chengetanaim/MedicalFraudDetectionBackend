import os
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
import dill

class MedicalInsuranceBase(SQLModel):
    RenalDiseaseIndicator:str
    ChronicDiseaseIndex:int
    InscClaimAmtReimbursed:int
    DeductibleAmtPaid:int
    IPAnnualReimbursementAmt:int
    OPAnnualReimbursementAmt:int
    IPAnnualDeductibleAmt:int
    OPAnnualDeductibleAmt:int
    treatment_intensity_score:float

class MedicalInsuranceCreate(MedicalInsuranceBase):
    pass

class MedicalInsurance(MedicalInsuranceBase, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    RenalDiseaseIndicator:str
    ChronicDiseaseIndex:int
    InscClaimAmtReimbursed:int
    DeductibleAmtPaid:int
    IPAnnualReimbursementAmt:int
    OPAnnualReimbursementAmt:int
    IPAnnualDeductibleAmt:int
    OPAnnualDeductibleAmt:int
    treatment_intensity_score:float

    prediction:str



db_url = 'postgresql://che:FQbwOTbBzxlmmPSrmNbpGH6utGdj5hJZ@dpg-d00ck0qli9vc739p2k10-a.oregon-postgres.render.com/medical_fraud_detection'
engine = create_engine(db_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()



@app.post("/predict")
def predict_medical_insurance_claims(medical_insurance_data: MedicalInsuranceCreate, session: SessionDep):
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    try:
        with open(model_path, "rb") as f:
            model = dill.load(f)
    except Exception as e:
        print("Failed to load model:", e)
        raise HTTPException(status_code=400, detail=f"Failed to load model: {e}")

    prediction = model(
    RenalDiseaseIndicator=medical_insurance_data.RenalDiseaseIndicator,
    ChronicDiseaseIndex=medical_insurance_data.ChronicDiseaseIndex,
    InscClaimAmtReimbursed=medical_insurance_data.InscClaimAmtReimbursed,
    DeductibleAmtPaid=medical_insurance_data.DeductibleAmtPaid,
    IPAnnualReimbursementAmt=medical_insurance_data.IPAnnualDeductibleAmt,
    OPAnnualReimbursementAmt=medical_insurance_data.OPAnnualDeductibleAmt,
    IPAnnualDeductibleAmt=medical_insurance_data.IPAnnualDeductibleAmt,
    OPAnnualDeductibleAmt=medical_insurance_data.OPAnnualDeductibleAmt,
    treatment_intensity_score=medical_insurance_data.treatment_intensity_score
)
    medical_insurance = MedicalInsurance( RenalDiseaseIndicator=medical_insurance_data.RenalDiseaseIndicator,
    ChronicDiseaseIndex=medical_insurance_data.ChronicDiseaseIndex,
    InscClaimAmtReimbursed=medical_insurance_data.InscClaimAmtReimbursed,
    DeductibleAmtPaid=medical_insurance_data.DeductibleAmtPaid,
    IPAnnualReimbursementAmt=medical_insurance_data.IPAnnualDeductibleAmt,
    OPAnnualReimbursementAmt=medical_insurance_data.OPAnnualDeductibleAmt,
    IPAnnualDeductibleAmt=medical_insurance_data.IPAnnualDeductibleAmt,
    OPAnnualDeductibleAmt=medical_insurance_data.OPAnnualDeductibleAmt,
    treatment_intensity_score=medical_insurance_data.treatment_intensity_score,
    prediction=prediction)
    
    session.add(medical_insurance)
    session.commit()
    session.refresh(medical_insurance)
    
    return medical_insurance


@app.get("/")
def read_predicted_results(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[MedicalInsurance]:
    predictions = session.exec(select(MedicalInsurance).offset(offset).limit(limit)).all()
    return predictions