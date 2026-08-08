from __future__ import annotations
from pathlib import Path
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.plugin import VotschClimateChamberPlugin


def test_plugin_descriptor_and_unconnected_library(tmp_path):
    descriptor=VotschClimateChamberPlugin.get_descriptor()
    assert descriptor["plugin_id"] == "votsch.climate_chamber"
    env=VotschClimateChamberPlugin.validate_environment()
    assert env["compatible"] is True
    lib=VotschClimateChamberPlugin.create_library(config={"default_resource":"SIM::plugin","managed_configuration_root":str(tmp_path)})
    assert lib.is_connected() is False


def test_driver_metadata_is_static():
    lib=VotschClimateChamberLibrary()
    info=lib.get_driver_information()
    assert info["package_version"] == "26.09"
    assert info["release_class"] == "D0"
    assert "temperature_control" in lib.get_driver_capabilities()
    assert lib.get_capability_model()


def test_configuration_roundtrip(tmp_path):
    lib=VotschClimateChamberLibrary(managed_configuration_root=str(tmp_path/"profiles"))
    schema=lib.get_driver_configuration_schema()
    assert schema["schema"]["type"] == "object"
    default=lib.get_driver_default_configuration()
    assert default["settings"]["connection"]["resource"] is None
    validated=lib.validate_driver_configuration(default)
    assert validated["valid"] is True
    saved=lib.save_driver_configuration("baseline", overwrite=True)
    assert saved["profile_name"] == "baseline"
    assert lib.list_driver_configuration_profiles()
    loaded=lib.load_driver_configuration("baseline")
    assert loaded["profile_name"] == "baseline"
    exported=lib.export_driver_configuration(str(tmp_path/"export.json"), overwrite=True)
    assert Path(exported["destination"]).exists()
    imported=lib.import_driver_configuration(str(tmp_path/"export.json"))
    assert imported["valid"] is True
    deleted=lib.delete_driver_configuration_profile("baseline", confirm=True)
    assert deleted["deleted"] is True


def test_public_keyword_metadata_is_explicit():
    import inspect
    from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
    names=[]
    for _,fn in inspect.getmembers(VotschClimateChamberLibrary, inspect.isfunction):
        if getattr(fn,"robot_name",None): names.append(fn.robot_name)
    assert "Connect" in names
    assert "Safe Shutdown" in names
    assert len(names) == len(set(n.casefold().replace(' ','').replace('_','') for n in names))
