# CS19 Capstone Project Final Artifacts

This repository contains the final artifact package for the CS19 capstone project. It includes the final presentation, scoring documentation, data dictionary package, notebooks, source data, scripts, and generated outputs used for the AAMI website accessibility and usability scoring workflow.

## Repository Contents

| Path | Description |
| --- | --- |
| `CS19-1_Final_Demo_Slide.pdf` | Final demo slide deck. |
| `SMP_Model_C_Scoring_Documentation_Handover_Pack.pdf` | Model C scoring documentation and handover pack. |
| `cs19_capstone_data&notebooks_package/` | Main notebook and data package for scoring, validation, tester quality rating, and presentation asset generation. |
| `final_data_dictionary_package/` | Final data dictionary, mapping rules, schema documentation, and master file inventory. |

## Main Notebook Package

The main working package is in `cs19_capstone_data&notebooks_package/`.

It contains:

- Proposal 1 / Model C scoring notebook.
- Proposal 2 time integration notebook.
- Manual review validation notebook.
- Tester quality rating notebook.
- Presentation asset generation notebook.
- Input data files, transcript segment files, helper scripts, and generated outputs.

For detailed setup and execution instructions, see:

`cs19_capstone_data&notebooks_package/README_How_To_Run.md`

## Run Order

Run the notebooks from inside `cs19_capstone_data&notebooks_package/` in this order:

1. `01_run_model_c_proposal1.ipynb`
2. `02_proposal2_time_integration.ipynb`
3. `03_manual_review_validation.ipynb`
4. `04_tester_quality_rating.ipynb`
5. `05_presentation_assets.ipynb`
6. `06_proposal2_rollup_outputs.ipynb`

The existing `outputs/` directory contains generated result files and presentation assets from the final run.

## Data Dictionary Package

The `final_data_dictionary_package/` directory documents the project data structure and output schemas. Key files include:

- `Final_Data_Dictionary_and_Master_File_Inventory.md`
- `final_data_dictionary.csv`
- `mapping_rules.csv`
- `master_file_inventory.csv`
- `observed_raw_field_profile.csv`
- `output_schema_documentation.csv`

## Notes

- This repository is an artifact handover package, not a minimal source-only codebase.
- The notebooks use relative paths and should be run from `cs19_capstone_data&notebooks_package/`.
- Generated outputs are included so the final results can be reviewed without re-running the full notebook chain.
