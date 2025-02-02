# Syncopy Developer Information

These development instructions are only relevant for people on the Syncopy core team.

## Making a new Release

### PyPI

At github:

* Keep latest version/changes to be release on the `dev` branch for now
* Set the new the package version in `pyproject.toml` and make sure release notes in the `CHANGELOG.md` file are up-to-date.
* After last commit on github, log into the local ESI GitLab installation from within ESI and wait for the sync from Github to happen. The CI pipeline should start all runnners:
  - stage 1: single machine for all architectures like intelllinux, intelwin, macos
  - stage 2: slurm / HPC runners
* Check + fix all failures. Note that the pipeline on the internal Gitlab differs from the CI run on Github in several ways:
  - parallel tests are run
  - platforms other than linux x64 are used
  - the ESI filesystem/cluster is available, so tests that require large local test data from the cluster's filesystem are run.
* Once tests are all green, you can do the following:  
  - in the gitlab "CI -- pipeline" tab, click on the name of the completed pipeline. You should see the stages. If parts of the pipeline stages 1 or 2 are still running, you can cancel them to unlock stage 3. There is a manual stage 3 'upload' entry named 'pypitest'. Click it to run the pypitest test deployment.
  - If it succeeded: there is a manual stage 4 'deploy' entry named 'pypideploy'. Click it to run the final deployment to pypi.
  - merge dev into master

This concludes the release to PyPI.

### Conda

Note: You need to release to PyPI first to start the conda release. Note that this requires that you have proper permissions on your Github account, i.e., you are a maintainer of the esi-syncopy package on conda-forge.

* Go to https://github.com/esi-neuroscience/esi-syncopy-feedstock. Note that it is a fork. Do **not** work on this one! Go to the original conda source repo (follow link on repo website) and clone that one to your private Github account.
* In your clone of the `esi-syncopy-feedstock` repo, in the file `recipe/meta.yaml`, do the following steps:
   - Update the version of the Syncopy package and use the file hash of the release on PyPI you did earlier (you can see the hash [here on PyPI](https://pypi.org/project/esi-syncopy/#files))
       * Beware: we typically have versions like `2023.07` on Github, and conda is fine with a version like that, too. However, PyPI removes the zero from `2023.07` in the package URL, so you cannot use  `{{ version }}` in the `source`..`url` field of the `meta.yml` file.
   - Check versions of packages in `meta.yml` here versus versions in `pyproject.toml`/`syncopy.yml` in the root of the Syncopy GitHub repo (they need not be 100% identical, but having to old versions in there may lead to security risks or unexpected behaviour with older/buggy package versions).
   - Fill out the `PR` check list
   - If the conditions listed in section [When to Rerender](https://conda-forge.org/docs/maintainer/updating_pkgs.html#when-to-rerender) in the conda documentation apply to the current change/release: request `@conda-forge-admin please rerender` via comment on GitHub. Important: this may require you to fork the feedstock repo to your private github account first and do it from there, because of github permission errors with organizations.
