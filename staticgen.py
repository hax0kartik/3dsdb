from os   import listdir
from json import load
from io   import open
import unicodedata

# harcode region shorthands
regions = {
    'GB': 'Europe/Australia',
    'US': 'USA',
    'JP': 'Japan',
    'TW': 'China',
    'KR': 'Korea'
}

# open static.html and write the head, faq, and table header
static = open('static.html', 'w', encoding='utf-8')
static.write(u"""
<!DOCTYPE html>
<html>
    <head>
        <title>3dsdb</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO"
            crossorigin="anonymous" type="text/css">
        <link rel="stylesheet" href="styles/design.css" type="text/css">
    </head>
    <body>
        <div class="container-fluid">
            <h2>FAQ:</h2>
            <ul>
                <li><b>Q) </b>How big is 1 3ds block?<br>
                <b>A) </b><i>1 3ds block = 128 kilobytes</i></li>
                <li><b>Q) </b>What is the use of QR(s)<br>
                <b>A) </b><i>The QR thumbnails on this page can be clicked then scanned with a 3DS to lead you directly to the title's eShop page.</i></li>
                <li><b>Q) </b>What is the use of TitleID(s)?<br>
                <b>A) </b><i>You need the titleid for cases such as when you want to extract a title using GM9.</i></li>
            </ul>
            <input id="search" placeholder="Search..." style="display: none;" aria-describedby="searchbox" type="text" class="form-control inputBox">
            <table class="table table-striped table-bordered table-hover table-dark">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>QR</th>
                        <th>TitleID</th>
                        <th>Version</th>
                        <th>Size</th>
                        <th>Publisher</th>
                        <th>Region</th>
                    </tr>
                </thead>
                <tbody>
""")

# get all the json files and iterate over them
files = [f for f in listdir('jsons') if f.startswith('list_')]
for file in files:
    region = regions[file[5:7]]
    titles = load(open('jsons/' + file))
    for title in titles:
        static.write(u"""
        <tr data-name="{0}">
            <td>{1}</td>
            <td>
                <a target="_blank" rel="noopener noreferrer" href="https://api.qrserver.com/v1/create-qr-code/?data={2}">
                    <img src="images/qrstock.png" class="qrstock">
                </a>
            </td>
            <td>{3}</td>
            <td>{4}</td>
            <td>{5}</td>
            <td>{6}</td>
            <td>{7}</td>
        </tr>
        """.format(''.join(c for c in unicodedata.normalize('NFD', title['Name']) if unicodedata.category(c) != 'Mn').lower(), title['Name'], title['UID'], title['TitleID'], title['Version'], title['Size'], title['Product Code'], region)) # accent removing code from https://stackoverflow.com/a/518232
        
# close the table and close static.html
static.write(u"""
                </tbody>
            </table>
        </div>
        <script>
            // search as-you-type
            var search = document.getElementById('search'),
                style  = document.createElement('style'),
                styletext = document.createTextNode('');
            style.appendChild(styletext);
            document.body.appendChild(style);
            search.style = '';
            search.oninput = function() {
                if (search.value) {
                    styletext.nodeValue = 'tr:not([data-name*="' + search.value.toLowerCase() + '"]) { display: none; }';
                } else styletext.nodeValue = '';
            }
        </script>
    </body>
</html>
""")
static.close()
