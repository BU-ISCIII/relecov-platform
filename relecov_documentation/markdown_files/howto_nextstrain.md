# How to use Nextstrain

Once you have correctly installed Nextstrain, following the steps described in the [README](https://github.com/Shettland/relecov-platform/tree/develop#install-nextstrain) you have to prepare your data and configuration files to run Nextstrain.

Once you have nextstrain installed, you can clone https://github.com/BU-ISCIII/nexstrain_relecov.git , copy it inside datasets/sars-cov-2/ ; for understanding, we will call this copy "build_folder".

Following the instructions explained [here](https://docs.nextstrain.org/en/latest/tutorials/creating-a-workflow.html) you will need to create the necessary files to run Nextstrain build. 

'/data' should contain all the sequences in a single FASTA file and a corresponding table of metadata describing those sequences in a tab-delimited text file. 
Each virus sequence record looks like the following, with the virus’s strain ID as the sequence name in the header line followed by the virus sequence.
```
>PAN/CDC_259359_V1_V3/2015
gaatttgaagcgaatgctaacaacagtatcaacaggttttattttggatttggaaacgag
agtttctggtcatgaaaaacccaaaaaagaaatccggaggattccggattgtcaatatgc
>PAN/CDC_356712_V1_V3/2015
caacaggttttattttggatttggaaacgagagtttctggtcatgaaaaacccaaaaaag
ccggaggattccggattgtcaatatgcccggaggattccggattgtcaatatgcccggaa
...
```

The header of the metadata table may vary depending on the metadata that you want to use, but you can find a reference [here](https://github.com/BU-ISCIII/nexstrain_relecov/blob/master/data/example_metadata.tsv). 

For a basic analysis not all the headers are necessary. The relecov's custom script [metadata_nextstrain_parser.py](https://github.com/BU-ISCIII/nexstrain_relecov/tree/master/data) can be run to parse the metadata processed with relecov-tools from json format to tsv format:
```
python metadata_nextstrain_parser.py relecov_metadata.json relecov_metadata.tsv
```

The next step would be to customize the config file 'relecov_data.yaml' to your needs.  You may find information on how to do this task [here](https://docs.nextstrain.org/projects/ncov/en/latest/reference/workflow-config-file.html).

Once these two files are set, you are ready to run Nextstrain. Change your directory to '/opt/nextstrain/cli-standalone/'. Now run the next command to start the nextstrain environment.
```
./nextstrain shell /opt/nextstrain/datasets/sars-cov-2/build_folder/:
```

The previous command should have redirected you to 'build_folder'. Now run the ncov workflow with:
```
nextstrain build . --configfile path/to/relecov_data.yaml
```
If the build is correct, you should see a prompt like the following, where N may vary depending on the given configuration:
```
Finished job 0.
N of N steps (100%) done
Complete log: /opt/nextstrain/datasets/sars-cov-2/build_folder/.snakemake/
```

Now you can visualize the results by running the next command:
```
nextstrain view auspice/
```

Once you are finished, you can type `exit` to close Nextstrain's terminal




