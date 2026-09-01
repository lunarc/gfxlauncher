from lhpcdt import scripts


def test_runscript_builds_expected_gfxlaunch_command(tmp_path):
    script_path = tmp_path / "paraview.sh"
    script_path.write_text(
        "#!/bin/sh\n"
        "##LDT category = \"Post Processing\"\n"
        "##LDT title = \"ParaView\"\n"
        "##LDT part = \"gpu\"\n"
        "##LDT group = \"ondemand\"\n"
        "##LDT vgl = \"yes\"\n"
        "echo test\n",
        encoding="utf-8",
    )

    run_script = scripts.RunScript(str(script_path))
    run_script.launcher = "gfxlaunch"

    assert run_script.launch_cmd == (
        'gfxlaunch --vgl --partition gpu --group ondemand --title "ParaView" --cmd %s'
        % str(script_path)
    )


def test_runscript_supports_direct_launch(tmp_path):
    script_path = tmp_path / "localtool.sh"
    script_path.write_text(
        "#!/bin/sh\n"
        "##LDT title = \"Local Tool\"\n"
        "##LDT no_launcher = \"yes\"\n"
        "echo local\n",
        encoding="utf-8",
    )

    run_script = scripts.RunScript(str(script_path))

    assert run_script.no_launcher is True
    assert run_script.launch_cmd == str(script_path)