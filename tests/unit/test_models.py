"""Tests for agents/models.py"""
import pytest
from agents.models import VerificationReport


def test_verification_report_required_fields():
    """VerificationReport debe requerir supported y relevant."""
    report = VerificationReport(supported="YES", relevant="YES")
    assert report.supported == "YES"
    assert report.relevant == "YES"


def test_verification_report_defaults():
    """VerificationReport debe tener defaults para campos opcionales."""
    report = VerificationReport(supported="NO", relevant="NO")
    assert report.unsupported_claims == []
    assert report.contradictions == []
    assert report.additional_details == ""


def test_verification_report_with_claims():
    """VerificationReport debe aceptar listas de claims."""
    report = VerificationReport(
        supported="NO",
        relevant="YES",
        unsupported_claims=["claim1", "claim2"],
        contradictions=["contradiction1"]
    )
    assert len(report.unsupported_claims) == 2
    assert len(report.contradictions) == 1


def test_to_report_supported_yes():
    """to_report debe formatear correctamente cuando es supported."""
    report = VerificationReport(supported="YES", relevant="YES")
    result = report.to_report()
    
    assert "**Supported:** YES" in result
    assert "**Unsupported Claims:** None" in result
    assert "**Contradictions:** None" in result
    assert "**Relevant:** YES" in result
    assert "**Additional Details:** None" in result


def test_to_report_supported_no():
    """to_report debe formatear correctamente cuando no es supported."""
    report = VerificationReport(
        supported="NO",
        relevant="YES",
        unsupported_claims=["claim1", "claim2"],
        contradictions=["contradiction1"],
        additional_details="Extra info"
    )
    result = report.to_report()
    
    assert "**Supported:** NO" in result
    assert "claim1, claim2" in result
    assert "contradiction1" in result
    assert "**Relevant:** YES" in result
    assert "Extra info" in result


def test_to_report_empty_claims():
    """to_report debe mostrar 'None' cuando no hay claims."""
    report = VerificationReport(supported="YES", relevant="YES")
    result = report.to_report()
    
    # Verificar que muestra None para listas vacías
    lines = result.split("\n")
    unsupported_line = next(l for l in lines if "Unsupported Claims" in l)
    assert "None" in unsupported_line


def test_verification_report_serialization():
    """VerificationReport debe serializarse correctamente."""
    report = VerificationReport(
        supported="YES",
        relevant="YES",
        unsupported_claims=["claim1"],
        additional_details="details"
    )
    
    # Verificar que se puede convertir a diccionario
    data = report.model_dump()
    assert data["supported"] == "YES"
    assert data["relevant"] == "YES"
    assert data["unsupported_claims"] == ["claim1"]
    assert data["additional_details"] == "details"


def test_verification_report_from_dict():
    """VerificationReport debe crearse desde un diccionario."""
    data = {
        "supported": "NO",
        "relevant": "YES",
        "unsupported_claims": ["test"],
        "contradictions": [],
        "additional_details": ""
    }
    
    report = VerificationReport(**data)
    assert report.supported == "NO"
    assert report.relevant == "YES"
    assert report.unsupported_claims == ["test"]
