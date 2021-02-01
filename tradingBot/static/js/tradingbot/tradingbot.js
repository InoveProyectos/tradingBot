$(document).ready(function(){
    $('#1d').click(function(e)
    {
        e.preventDefault();
        getGraph('1d');
    });
    $('#5d').click(function(e)
    {
        e.preventDefault();
        getGraph('5d');
    });
    $('#1M').click(function(e)
    {
        e.preventDefault();
        getGraph('1M');
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

    function getGraph(inteval) {

        var url = window.location.origin + window.location.pathname + '/graph'

        $.post(url, {inteval: inteval},
            function(graph_data) {
                var graph = graph_data
                Plotly.newPlot("graph-0", graph.data, graph.layout);       
            }
        );
    }

});