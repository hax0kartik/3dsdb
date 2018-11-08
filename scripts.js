const getJSON = (path, region) => {
  const t0 = performance.now();
  const xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        const t1 = performance.now();

        console.log(`http call took ${t1 - t0} milliseconds.`);
        const text = JSON.parse(xhr.responseText);
        // EXTRACT VALUE FOR HTML HEADER.
        const col = [];

        for (let i = 0; i < text.length; i++) {
          for (const key in text[i]) {
            if (col.indexOf(key) === -1) {
              col.push(key);
            }
          }
        }
        col.push('Region');
        var t = $('#dataTable').DataTable();
        for(let i = 0; i < text.length; i++)
        {
          var link = "https://api.qrserver.com/v1/create-qr-code/?data=ESHOP://" + text[i][col[1]];
          var qr = `<a target="_blank" rel="noopener noreferrer" href="${link}"><img src="images/qrstock.png" height=46 width=46></img>`;
          t.row.add([
            text[i][col[0]],
            qr,
            text[i][col[2]],
            text[i][col[3]],
            text[i][col[4]],
            region
          ]);
        }
        t.draw(false);
      }
    }
  };
  xhr.open('GET', path, true);
  xhr.send();
  console.log(`Finished`)
};

const populateTable = () => {
  var regions = ['GB', 'US', 'JP', 'TW', 'KR'];
  var display_regions = ['Europe/Australia', 'USA', 'Japan', 'China', 'Korea'];

  regions.forEach((region, index) => {
    return getJSON(
      `https://raw.githubusercontent.com/hax0kartik/3dsdb/master/jsons/list_${region}.json`,
      display_regions[index])
  });
  console.log(`DONE.`)
};

const storeColorMode = (mode) => {
  localStorage.setItem('colorMode', JSON.stringify({light: mode}));
};

const toggleColorMode = () => {
  if ($('#switch-normal').is(":checked")) {
    $('body').addClass('lightMode')
    $('.inputBox').addClass('lightMode');
    $('#tableHeader').addClass('table-info');
    $('#dataTable').removeClass('table-dark');
    $('#tableHeader').removeClass('thead-dark');

    return storeColorMode(true)
  } else {
    $('body').removeClass('lightMode')
    $('.inputBox').removeClass('lightMode');
    $('#tableHeader').removeClass('table-info');
    $('#dataTable').addClass('table-dark');
    $('#tableHeader').addClass('thead-dark');

    return storeColorMode(false)
  }
};

const loadLastColor = () => {
  const storedMode = localStorage.getItem('colorMode');

  if(storedMode && JSON.parse(storedMode).light) {
    $('#switch-normal').prop('checked', true);
    toggleColorMode();
  }
};