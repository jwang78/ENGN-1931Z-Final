function doGet(e) {
  var name = e.parameter["name"];
  var error = e.parameter["error"];
  var timeSpent = e.parameter["time"];
  var notesPlayed = e.parameter["notes"];
  if (!name || !error || !timeSpent || !notesPlayed) {
    return HtmlService.createHtmlOutput("Missing required parameter");
  }
  var spreadsheet = SpreadsheetApp.openByUrl("https://docs.google.com/spreadsheets/d/1pe-gYKsWVuZ2fmO6iI25ZzaY6SFdxAUBNKfQlV02ZHE/edit#gid=0"); // Insert spreadsheet url here
  spreadsheet.appendRow([name, error, notesPlayed, timeSpent]);
  return HtmlService.createHtmlOutput("Success!");
}
