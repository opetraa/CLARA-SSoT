"""공용 테스트 픽스처 모듈."""
# tests/conftest.py
from pathlib import Path

import pytest

from tractara.normalization.doc_mapper import build_doc_baseline
from tractara.parsing.xml_parser import parse_xml

# ---------------------------------------------------------------------------
# S1000D Golden Fixture — 테스트 XML → ParsedDocument → DOC Baseline JSON
# ---------------------------------------------------------------------------
_S1000D_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<dmodule>
    <identAndStatusSection>
        <dmAddress>
            <dmIdent>
                <dmCode modelIdentCode="BIKE" systemDiffCode="A"
                        systemCode="00" subSystemCode="0"
                        subSubSystemCode="0" assyCode="00"
                        disassyCode="00" disassyCodeVariant="A"
                        infoCode="922" infoCodeVariant="A"
                        itemLocationCode="D"/>
            </dmIdent>
            <dmTitle>
                <techName>Bicycle</techName>
                <infoName>Maintenance</infoName>
            </dmTitle>
        </dmAddress>
        <dmStatus issueType="new">
            <skillLevel skillLevelCode="sk01"/>
            <applic id="app-0001">
                <displayText><simplePara>Test Applic</simplePara></displayText>
                <evaluate andOr="and">
                    <assert applicPropertyIdent="type"
                            applicPropertyType="prodattr"
                            applicPropertyValues="Bike"/>
                </evaluate>
            </applic>
            <qualityAssurance>
                <firstVerification verificationType="tabtop"/>
            </qualityAssurance>
            <applicCrossRefTableRef>
                <dmRef><dmRefIdent><dmCode modelIdentCode="BIKE"
                    systemDiffCode="A" systemCode="00" subSystemCode="0"
                    subSubSystemCode="0" assyCode="00" disassyCode="00"
                    disassyCodeVariant="A" infoCode="00W"
                    infoCodeVariant="A"
                    itemLocationCode="D"/></dmRefIdent></dmRef>
            </applicCrossRefTableRef>
            <brexDmRef>
                <dmRef><dmRefIdent><dmCode modelIdentCode="BIKE"
                    systemDiffCode="A" systemCode="00" subSystemCode="0"
                    subSubSystemCode="0" assyCode="00" disassyCode="00"
                    disassyCodeVariant="A" infoCode="022"
                    infoCodeVariant="A"
                    itemLocationCode="D"/></dmRefIdent></dmRef>
            </brexDmRef>
        </dmStatus>
    </identAndStatusSection>
    <content>
        <procedure>
            <preliminaryRqmts>
                <reqCondGroup><noConds/></reqCondGroup>
                <reqSafety><noSafety/></reqSafety>
            </preliminaryRqmts>
            <mainProcedure>
                <levelledPara>
                    <title>Removal of Wheel</title>
                    <warning>Always wear safety goggles.</warning>
                    <note><notePara>Ensure the bike is on a stand.</notePara></note>
                    <proceduralStep applicRefId="app-0001">
                        <note><notePara>This is an empty step note.</notePara></note>
                    </proceduralStep>
                    <proceduralStep applicRefId="app-0001">
                        <reqCondNo id="rc1">Release pressure</reqCondNo>
                        <supportEquipDescr>Wrench</supportEquipDescr>
                        <para>Use wrench to loosen the bolt.</para>
                        <torque>
                            <torqueValue>50</torqueValue>
                            <torqueUnit>Nm</torqueUnit>
                        </torque>
                    </proceduralStep>
                </levelledPara>
            </mainProcedure>
            <closeRqmts>
                <reqCondGroup><noConds/></reqCondGroup>
            </closeRqmts>
        </procedure>
    </content>
</dmodule>
"""


@pytest.fixture
def s1000d_xml_path(tmp_path: Path) -> Path:
    """S1000D 테스트 XML 파일 경로를 반환합니다."""
    p = tmp_path / "golden_s1000d.xml"
    p.write_text(_S1000D_XML, encoding="utf-8")
    return p


@pytest.fixture
def s1000d_parsed(s1000d_xml_path: Path):
    """S1000D XML → ParsedDocument."""
    return parse_xml(s1000d_xml_path)


@pytest.fixture
def s1000d_doc_json(s1000d_parsed):
    """S1000D ParsedDocument → DOC Baseline JSON dict."""
    return build_doc_baseline(s1000d_parsed)


# ---------------------------------------------------------------------------
# JATS Golden Fixture
# ---------------------------------------------------------------------------
_JATS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<article>
    <front>
        <article-meta>
            <title-group>
                <article-title>A Study on Nuclear Safety</article-title>
            </title-group>
            <contrib-group>
                <contrib contrib-type="author">
                    <name><surname>Doe</surname><given-names>John</given-names></name>
                </contrib>
            </contrib-group>
        </article-meta>
    </front>
    <body>
        <sec>
            <title>1. Introduction</title>
            <p>Safety is paramount <xref ref-type="bibr" rid="ref1">[1]</xref>.</p>
            <sec>
                <title>1.1 Background</title>
                <p>Background details.</p>
            </sec>
        </sec>
        <sec>
            <title>2. Methods</title>
            <p>We used the following equation:</p>
            <disp-formula>E = mc^2</disp-formula>
        </sec>
    </body>
    <back>
        <ref-list>
            <ref id="ref1">DOE, 2024</ref>
        </ref-list>
    </back>
</article>
"""


@pytest.fixture
def jats_xml_path(tmp_path: Path) -> Path:
    """JATS 테스트 XML 파일 경로를 반환합니다."""
    p = tmp_path / "golden_jats.xml"
    p.write_text(_JATS_XML, encoding="utf-8")
    return p


@pytest.fixture
def jats_parsed(jats_xml_path: Path):
    """JATS XML → ParsedDocument."""
    return parse_xml(jats_xml_path)


@pytest.fixture
def jats_doc_json(jats_parsed):
    """JATS ParsedDocument → DOC Baseline JSON dict."""
    return build_doc_baseline(jats_parsed)
