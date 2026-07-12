const fs = require('fs');
const path = require('path');
const { generate } = require('@pdfme/generator');
const {
    text,
    multiVariableText,
    table,
    line,
    rectangle,
    ellipse,
    image,
    svg,
    barcodes,
} = require("@pdfme/schemas");



// Define plugins object with proper JavaScript syntax
const plugins = {
    text,
    multiVariableText,
    table,
    line,
    rectangle,
    ellipse,
    image,
    svg,
};

const args = process.argv.slice(2);
if (args.length < 3) {
    console.error('Usage: node main.js <template.json> <data.json> <output.pdf>');
    process.exit(1);
}

console.log('Received args:', args);

const [templateFile, dataFile, outputFile] = args;

let template, inputs;

try {
    template = JSON.parse(fs.readFileSync(path.resolve(templateFile), 'utf8'));
    console.log('Template loaded successfully');
} catch (err) {
    console.error('Error parsing template JSON:', err.message);
    process.exit(2);
}

try {
    inputs = JSON.parse(fs.readFileSync(path.resolve(dataFile), 'utf8'));
    if (!Array.isArray(inputs)) {
        console.error('❌ Error: inputs must be an array');
        process.exit(3);
    }
    console.log('Data loaded successfully, inputs count:', inputs.length);
} catch (err) {
    console.error('Error parsing data JSON:', err.message);
    process.exit(3);
}

(async () => {
    try {
        console.log('Starting PDF generation...');
        const pdfBuffer = await generate({ 
            template, 
            inputs, 
            plugins 
        });
        
        console.log('PDF generated, writing to file...');
        fs.writeFileSync(outputFile, pdfBuffer);

        if (fs.existsSync(outputFile)) {
            const stats = fs.statSync(outputFile);
            console.log(`✅ PDF generated successfully as ${outputFile} (${stats.size} bytes)`);
            process.exit(0);
        } else {
            console.error(`❌ Failed to write PDF to ${outputFile}`);
            process.exit(4);
        }
    } catch (err) {
        console.error('Error generating PDF:', err.message);
        console.error('Stack trace:', err.stack);
        process.exit(5);
    }
})();