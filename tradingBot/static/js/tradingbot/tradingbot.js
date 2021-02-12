$(document).ready(function(){
    $('#1M').click(function(e)
    {
        e.preventDefault();
        getGraph('1M');
    });
    $('#2M').click(function(e)
    {
        e.preventDefault();
        getGraph('2M');
    });
    $('#3M').click(function(e)
    {
        e.preventDefault();
        getGraph('3M');
    });
    $('#6M').click(function(e)
    {
        e.preventDefault();
        getGraph('6M');
    });
    $('#1Y').click(function(e)
    {
        e.preventDefault();
        getGraph('1Y');
    });
    $('#instruments').change(function(e)
    {
        e.preventDefault();
        getGraph('1Y');
    });

    function getGraph(inteval) {

        var url = window.location.origin + window.location.pathname + '/graph'

        var instrument = document.getElementById("instruments").value;

        $.post(url, {inteval: inteval, instrument:instrument},
            function(graph_data) {
                var graph = graph_data
                Plotly.newPlot("graph-0", graph.data, graph.layout);       
            }
        );
    }

});