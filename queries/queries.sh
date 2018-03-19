# multifasta
http --follow post "$WF_SERVER/run?wf=https://raw.githubusercontent.com/esanzgar/webservice-cwl/master/docker_cwls/phobius-multifasta.cwl" < array_output.json

# breaks cwltool
http --follow post "$WF_SERVER/run?wf=https://raw.githubusercontent.com/esanzgar/webservice-cwl/webprod/docker_cwls/ncbiblast.cwl" < 2-lines-sequence.json
