from enum import Enum
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

class YesNo(str, Enum):
    No = 'No'
    Yes = 'Yes'

def detect_fraud(
    RenalDiseaseIndicator: YesNo,
    ChronicDiseaseIndex: int,
    InscClaimAmtReimbursed: float,
    DeductibleAmtPaid: float,
    IPAnnualReimbursementAmt: float,
    OPAnnualReimbursementAmt: float,
    IPAnnualDeductibleAmt: float,
    OPAnnualDeductibleAmt: float,
    treatment_intensity_score: float = 0.0  # optional: 0=low, 1=high
) -> str:
    """
    Returns 'Fraud' or 'Not Fraud' based on input values and defined heuristics.

    :param RenalDiseaseIndicator: 'Y' or 'N'
    :param ChronicDiseaseIndex: Integer (0 = no chronic diseases)
    :param InscClaimAmtReimbursed: Reimbursement amount for this claim
    :param DeductibleAmtPaid: Deductible amount paid by patient
    :param IPAnnualReimbursementAmt: Annual inpatient reimbursement
    :param OPAnnualReimbursementAmt: Annual outpatient reimbursement
    :param IPAnnualDeductibleAmt: Annual inpatient deductible
    :param OPAnnualDeductibleAmt: Annual outpatient deductible
    :param treatment_intensity_score: Optional score (0.0–1.0) representing treatment intensity
    """
    # Rule 1: High treatment but no chronic disease
    if ChronicDiseaseIndex == 0 and treatment_intensity_score > 0.7:
        return "Fraud"

    # Rule 2: Unusually high reimbursement
    if InscClaimAmtReimbursed > 50000:
        return "Fraud"

    # Rule 3: Minimal deductible paid but high reimbursement
    if DeductibleAmtPaid < 100 and InscClaimAmtReimbursed > 10000:
        return "Fraud"

    # Rule 4: Suspicious spikes in annual reimbursements
    if IPAnnualReimbursementAmt > 100000 or OPAnnualReimbursementAmt > 80000:
        return "Fraud"

    # Rule 5: Deductible manipulation patterns
    if IPAnnualDeductibleAmt < 200 and OPAnnualDeductibleAmt < 200 and (IPAnnualReimbursementAmt + OPAnnualReimbursementAmt) > 50000:
        return "Fraud"

    return "Not Fraud"






@app.post("/predict")
def predict_medical_insurance_claims(medical_insurance_data: MedicalInsuranceCreate, session: SessionDep):
    prediction = detect_fraud(
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