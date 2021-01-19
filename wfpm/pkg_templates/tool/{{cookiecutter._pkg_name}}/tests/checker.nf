#!/usr/bin/env nextflow

/*
 This is an auto-generated checker workflow, please update as needed
*/

nextflow.enable.dsl = 2
version = '{{ cookiecutter.pkg_version }}'  // tool version

// universal params
params.publish_dir = ""
params.container_version = ""

// tool specific parmas go here, add / change as needed
params.input_file = ""
params.expected_output = ""

include { {{ cookiecutter._process_name }} } from '../{{ cookiecutter._pkg_name }}'

Channel
  .fromPath(params.input_file, checkIfExists: true)
  .set { input_file }


process file_diff {
  container "{{ cookiecutter.container_registry }}/{{ cookiecutter.registry_account|lower }}/{{ cookiecutter._repo_name }}.{{ cookiecutter._pkg_name }}:${params.container_version ?: version}"

  input:
    path file1
    path file2

  output:
    stdout()

  script:
    """
    # TODO: remove date field before comparison
    diff ${file1} ${file2} && ( echo "Test PASSED" && exit 0 ) || ( echo "Test FAILED, output file mismatch." && exit 1 )
    """
}


workflow checker {
  take:
    input_file
    expected_output

  main:
    {{ cookiecutter._process_name }}(
      input_file
    )

    file_diff(
      {{ cookiecutter._process_name }}.out.output,
      expected_output
    )
}


workflow {
  checker(
    file(params.input_file),
    file(params.expected_output)
  )
}