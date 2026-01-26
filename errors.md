(base) hy.joo@nautilus:~/2026/gitprojects/ai-memory-agent$ pip install -e .
Obtaining file:///home/hy.joo/2026/gitprojects/ai-memory-agent
  Installing build dependencies ... done
  Checking if build backend supports build_editable ... done
  Getting requirements to build editable ... done
  Installing backend dependencies ... done
  Preparing editable metadata (pyproject.toml) ... error
  error: subprocess-exited-with-error
  
  × Preparing editable metadata (pyproject.toml) did not run successfully.
  │ exit code: 1
  ╰─> [53 lines of output]
      Traceback (most recent call last):
        File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 195, in prepare_metadata_for_build_editable
          hook = backend.prepare_metadata_for_build_editable
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      AttributeError: module 'hatchling.build' has no attribute 'prepare_metadata_for_build_editable'
      
      During handling of the above exception, another exception occurred:
      
      Traceback (most recent call last):
        File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 389, in <module>
          main()
          ~~~~^^
        File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 373, in main
          json_out["return_val"] = hook(**hook_input["kwargs"])
                                   ~~~~^^^^^^^^^^^^^^^^^^^^^^^^
        File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py", line 204, in prepare_metadata_for_build_editable
          whl_basename = build_hook(metadata_directory, config_settings)
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/build.py", line 83, in build_editable
          return os.path.basename(next(builder.build(directory=wheel_directory, versions=["editable"])))
                                  ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/plugin/interface.py", line 157, in build
          artifact = version_api[version](directory, **build_data)
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/wheel.py", line 522, in build_editable
          return self.build_editable_detection(directory, **build_data)
                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/wheel.py", line 534, in build_editable_detection
          for included_file in self.recurse_selected_project_files():
                               ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/plugin/interface.py", line 182, in recurse_selected_project_files
          if self.config.only_include:
             ^^^^^^^^^^^^^^^^^^^^^^^^
        File "/home/hy.joo/miniconda3/lib/python3.13/functools.py", line 1026, in __get__
          val = self.func(instance)
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/config.py", line 715, in only_include
          only_include = only_include_config.get("only-include", self.default_only_include()) or self.packages
                                                                 ~~~~~~~~~~~~~~~~~~~~~~~~~^^
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/wheel.py", line 268, in default_only_include
          return self.default_file_selection_options.only_include
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "/home/hy.joo/miniconda3/lib/python3.13/functools.py", line 1026, in __get__
          val = self.func(instance)
        File "/tmp/pip-build-env-gdtrpf3o/overlay/lib/python3.13/site-packages/hatchling/builders/wheel.py", line 256, in default_file_selection_options
          raise ValueError(message)
      ValueError: Unable to determine which files to ship inside the wheel using the following heuristics: https://hatch.pypa.io/latest/plugins/builder/wheel/#default-file-selection
      
      The most likely cause of this is that there is no directory that matches the name of your project (ai_memory_agent).
      
      At least one file selection option must be defined in the `tool.hatch.build.targets.wheel` table, see: https://hatch.pypa.io/latest/config/build/
      
      As an example, if you intend to ship a directory named `foo` that resides within a `src` directory located at the root of your project, you can define the following:
      
      [tool.hatch.build.targets.wheel]
      packages = ["src/foo"]
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
error: metadata-generation-failed

× Encountered error while generating package metadata.
╰─> from file:///home/hy.joo/2026/gitprojects/ai-memory-agent

note: This is an issue with the package mentioned above, not pip.
hint: See above for details.