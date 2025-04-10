// CSV to JSON converter for trade data
const fs = require('fs');
const path = require('path');

// Function to parse CSV data
function parseCSV(csvData) {
  const lines = csvData.split('\n');
  const result = [];
  
  // Skip header line
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    // Split by tab or comma, handle quotes
    const fields = line.split(/\t|,/).map(field => field.replace(/"/g, '').trim());
    
    if (fields.length >= 5) {
      result.push({
        country: fields[0],
        indicator: fields[1],
        code: fields[2],
        date: fields[3],
        value: parseFloat(fields[4])
      });
    }
  }
  
  return result;
}

// Function to convert parsed data to structured JSON
function convertToJSON(data) {
  const jsonData = {};
  
  data.forEach(item => {
    // Skip invalid entries
    if (!item.country || isNaN(item.value)) return;
    
    // Extract year from date
    const year = item.date.split('-')[0];
    
    // Initialize country object if it doesn't exist
    if (!jsonData[item.country]) {
      jsonData[item.country] = {
        exports: {}, // 对中国出口
        imports: {}  // 从中国进口
      };
    }
    
    // Add data based on indicator type
    if (item.indicator === "对中国出口") {
      jsonData[item.country].exports[year] = item.value;
    } else if (item.indicator === "从中国进口") {
      jsonData[item.country].imports[year] = item.value;
    }
  });
  
  return jsonData;
}

// Main function
function convertCSVtoJSON() {
  try {
    // Read CSV file
    const csvPath = path.join(__dirname, 'data', 'data.csv');
    const outputPath = path.join(__dirname, 'data', 'trade_data.json');
    
    // Read file as buffer to handle various encodings
    const buffer = fs.readFileSync(csvPath);
    
    // Try to decode with UTF-8 first
    let csvContent;
    try {
      csvContent = buffer.toString('utf-8');
    } catch (e) {
      // If UTF-8 fails, try alternate approach
      csvContent = buffer.toString();
    }
    
    // Parse CSV and convert to JSON
    const parsedData = parseCSV(csvContent);
    const jsonData = convertToJSON(parsedData);
    
    // Handle Chinese characters and manual replacements for encoding issues
    const replaceMap = {
      "闃垮瘜姹?": "阿富汗",
      "瀵逛腑鍥藉嚭鍙?": "对中国出口",
      "浠庝腑鍥借繘鍙?": "从中国进口",
      // Add more replacements as needed based on your data
      "闃垮彜姹?": "阿古汗",
      "闃垮彜濮?": "阿古巴",
      "闃垮叞閰?": "阿兰酋",
      "闃垮叞閰熀": "阿联酋",
      "闃垮叞鑱旂偣": "阿联酋"
    };
    
    // Add specific country handling for known data issues
    for (const country in jsonData) {
      // Apply replacements if needed
      const normalizedCountry = replaceMap[country] || country;
      
      // If country name was normalized, ensure data is merged correctly
      if (normalizedCountry !== country) {
        if (!jsonData[normalizedCountry]) {
          jsonData[normalizedCountry] = {
            exports: {},
            imports: {}
          };
        }
        
        // Merge export data
        Object.assign(jsonData[normalizedCountry].exports, jsonData[country].exports);
        
        // Merge import data
        Object.assign(jsonData[normalizedCountry].imports, jsonData[country].imports);
        
        // Remove the original entry
        delete jsonData[country];
      }
    }
    
    // Format the JSON with proper spacing
    const jsonContent = JSON.stringify(jsonData, null, 2);
    
    // Write JSON to file
    fs.writeFileSync(outputPath, jsonContent);
    
    console.log(`Successfully converted CSV to JSON. Output saved to ${outputPath}`);
    console.log(`Total countries: ${Object.keys(jsonData).length}`);
    
    return jsonData;
  } catch (error) {
    console.error('Error converting CSV to JSON:', error);
    return null;
  }
}

// Execute the conversion
const result = convertCSVtoJSON();

// List first few countries as a sample
console.log("\nSample of the JSON data:");
const sampleEntries = Object.entries(result || {}).slice(0, 3);
sampleEntries.forEach(([country, data]) => {
  console.log(`\nCountry: ${country}`);
  console.log("Exports to China:");
  console.log(data.exports);
  console.log("Imports from China:");
  console.log(data.imports);
}); 