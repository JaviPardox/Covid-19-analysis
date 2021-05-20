

function vaccine_chart(country,type){

    // Keep track of the country being displayed
    last_country = country;

    d3.json("http://localhost:5000/" + type).then(function(data){

        // Get the data for that country
        result = data[country];

        // Get all vaccines manufacturers
        var vaccines = Object.keys(result);

        // Declare array for chart data
        all_data = []

        // Push each vaccine data into array
        vaccines.forEach(function(vaccine){

            all_data.push(result[vaccine])

        })
        
        // Chart layout
        var layout = {
            title:'Total vaccinations in ' + country,
            xaxis: {
                title: 'Date',
                showgrid: true,
                zeroline: true
              },
              yaxis: {
                title: 'Total Vaccinations',
                showline: true
              }
          };

        
        if(type === 'allvaccines_change'){  
         
            layout.title = 'Daily vaccinatios in ' + country
            layout.yaxis.title = 'Daily vaccinations'

        }

        // Plot data
        console.log("good format") 
        console.log(all_data)
        Plotly.newPlot('plot', all_data, layout);


    })

}

function newVaccineChart(countries,type){

    //console.log("countries: " + countries)

    d3.json("http://localhost:5000/" + type).then(function(data){

        // Get all the data for each country
        results = []
        countries.forEach(function(country){
            result = data[country]
            results.push(result)
        })
        
        //console.log("countries results:")
        //console.log(results)

        // Index each vaccine manufacturer for each country and push it to array
        all_data = []
        results.forEach(function(results_data){
            
            var vaccines = Object.keys(results_data);
            vaccines.forEach(function(vaccine){

                all_data.push(results_data[vaccine])

            })
                
        })
        
        //console.log(all_data)

        // Chart layout
        var layout = {
            title: 'Total vaccinations in ' + countries,
            xaxis: {
                title: 'Date',
                showgrid: true,
                zeroline: true
            },
            yaxis: {
                title: 'Total Vaccinations',
                showline: true
            }
        };


        if (type === 'allvaccines_change') {

            layout.title = 'Daily vaccinatios in ' + countries
            layout.yaxis.title = 'Daily vaccinations'

        }

        Plotly.newPlot('plot_checkbox', all_data, layout);

    })



}

function init_vacc(){

    // Select container
    var selector = d3.select("#selDataset")
    var checkbox_sel = d3.select("#checkboxid")

    // Get the data
    d3.json("http://localhost:5000/allvaccines").then(function(data){

        // Get the keys 
        var countries = Object.keys(data);

        // Append each key to the container
        countries.forEach(function(name){

            selector
            .append("option")
            .text(name)
            .property("value",name);

        })

        // Append countries as checkboxes
        // Id works as index to access the label tag an populate it with 
        // Input tag and its attributes
        var id_checkbox = 0;
        countries.forEach(function(name){

            checkbox_sel
            .append('label')
                .attr('for',"a"+id_checkbox)
                .text(name)
            .append("input")
                .attr("type", "checkbox")
                .attr("id","a"+id_checkbox)
                .attr("value",name)
                .attr("onclick","addTrace(this.value)");

            checkbox_sel
            .append("br")
            
            id_checkbox++;

        })
        // Reset id index
        id_checkbox = 0;

        // Initialize the chart with first country and vaccination data address
        vaccine_chart(countries[0],'allvaccines');
        newVaccineChart(countries_selected,'allvaccines')

    })

}

function optionChanged(new_country){

    // Value from well changed
    vaccine_chart(new_country,vacc_type);
}

function vaccChanged(type){

    // Keep track of the data displayed
    vacc_type = type;
    vaccine_chart(last_country,type);
    newVaccineChart(countries_selected,type)

}

function addTrace(name){
    
    // Check if country selected is already in array
    if(countries_selected.includes(name)){

        // If it's in array, it means that the checkbox was unselected, delete country
        countries_selected.splice(countries_selected.indexOf(name),1)
    }
    else{

        // Else, add country to the array
        countries_selected.push(name)
    }

    // Create new chart after a change in the checkbox list
    newVaccineChart(countries_selected,vacc_type)
}

// Array that holds the amount of countries that are currently being displayed 
var countries_selected = [];

// Initialize global variables, used to keep track of the data being displayed
var last_country = 'Chile';
var vacc_type = 'allvaccines';

init_vacc();