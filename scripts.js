// Mapping of regions
const COVID_REGION_MAPPING = {
    "1": "North Scotland",
    "2": "South Scotland",
    "3": "North West England",
    "4": "North East England",
    "5": "Yorkshire",
    "6": "North Wales",
    "7": "South Wales",
    "8": "West Midlands",
    "9": "East Midlands",
    "10": "East England",
    "11": "South West England",
    "12": "South England",
    "13": "London",
    "14": "South East England",
    "15": "England",
    "16": "Scotland",
    "17": "Wales"
};

// Populate the dropdown with regions from the mapping
const regionDropdown = document.getElementById('region');
for (const [key, value] of Object.entries(COVID_REGION_MAPPING)) {
    const option = document.createElement('option');
    option.value = key;
    option.innerText = value;
    regionDropdown.appendChild(option);
}

document.getElementById('fetchData').addEventListener('click', function () {
    const fromDate = document.getElementById('from_date').value;
    const toDate = document.getElementById('to_date').value;
    const regionId = document.getElementById('region').value; // Fetch selected region id

    fetch(`http://localhost:5000/region-data/${regionId}/${fromDate}/${toDate}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('output').style.display = 'block';

            // Carbon intensity data
            const carbonData = data.carbon_intensity.data.data;

            let totalIntensity = 0;
            if (Array.isArray(carbonData)) {
                carbonData.forEach(entry => {
                    totalIntensity += (entry.intensity && entry.intensity.forecast) || 0;
                });
            } else {
                console.error('Carbon data is not an array:', carbonData);
            }
            const avgIntensity = totalIntensity / (carbonData.length || 1);
            document.getElementById('carbon_data').innerText = `Average Intensity: ${avgIntensity.toFixed(2)}`;

            // Covid data 
            const covidDataEntries = data.covid_data.data;
            let totalCases = 0;
            if (Array.isArray(covidDataEntries)) {
                covidDataEntries.forEach(entry => {
                    totalCases += entry.cumulativeCases || 0;
                });
            } else {
                console.error('Covid data is not an array:', covidDataEntries);
            }
            const avgCases = totalCases / (covidDataEntries.length || 1);
            document.getElementById('covid_data').innerText = `Average Daily Cases: ${avgCases.toFixed(2)}`;
        })
        .catch(error => {
            console.error('There was an error fetching the data:', error);
        });
});
