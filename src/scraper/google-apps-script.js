/**
 * Simple TicketSwap Scraper for Google Apps Script
 *
 * SETUP:
 * 1. Open your Google Sheet on the tab you want to write to
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code and save
 * 4. Run scrapeTicketSwapData() whenever you want new data
 */

function scrapeTicketSwapData() {
  const TICKETSWAP_URL = 'https://www.ticketswap.com/event/lowlands-festival-2025/weekend-tickets/880608ba-8652-49dc-9ddb-05a300cd6c97/4255719';

  try {
    const sheet = SpreadsheetApp.getActiveSheet();

    // Create temporary sheet for IMPORTXML
    const tempSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('temp');
    const formula = `=IMPORTXML("${TICKETSWAP_URL}", "//text()[contains(., 'available') or contains(., 'price') or contains(., '€') or contains(., 'EUR')]")`;
    tempSheet.getRange('A1').setFormula(formula);

    // Wait for formula to load
    Utilities.sleep(5000);

    // Get the results and clean up
    const range = tempSheet.getDataRange();
    const results = range.getValues();
    SpreadsheetApp.getActiveSpreadsheet().deleteSheet(tempSheet);

    // Parse the data
    const fullText = results.flat().join(' ');

    // Extract ticket counts from JSON data
    const available = extractNumber(fullText, /"availableTicketsCount"\s*:\s*(\d+)/) ||
                     extractNumber(fullText, /availableTicketsCount[^0-9]*(\d+)/) ||
                     extractNumber(fullText, /(\d+)\s*available/i);

    const sold = extractNumber(fullText, /"soldTicketsCount"\s*:\s*(\d+)/) ||
                extractNumber(fullText, /soldTicketsCount[^0-9]*(\d+)/) ||
                extractNumber(fullText, /(\d+)\s*sold/i);

    const wanted = extractNumber(fullText, /"ticketAlertsCount"\s*:\s*(\d+)/) ||
                  extractNumber(fullText, /ticketAlertsCount[^0-9]*(\d+)/) ||
                  extractNumber(fullText, /(\d+)\s*wanted/i);

    // Add row to sheet
    const timestamp = new Date();
    const status = available ? 'Success' : 'Failed';
    const row = [timestamp, available || 'N/A', sold || 'N/A', wanted || 'N/A', status];

    sheet.appendRow(row);

  } catch (error) {
    console.error('Error:', error);
  }
}

function extractNumber(text, pattern) {
  const match = text.match(pattern);
  return match ? parseInt(match[1]) : null;
}
