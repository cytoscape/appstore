var SubmitAPI = (function($) {
  /*
  Add a message to the pom status message area. Used for error and warning boxes.
  */
   function addStatusMsg(type, msg) {
    $('#pom-status-msgs').append('<div class="alert alert-' + type + '">' + msg + '</div>');
  }

 /*
 Given an unparsed string containing XML, try to get Maven Pom coordinates (i.e. group ID, artifact ID, version).
 */
  var PomAttrs = ['groupId', 'artifactId', 'version'];
  function extractPomAttrs(xmlText) {
    var doc;
    try {
      doc = $($.parseXML(xmlText));
    } catch(error) {
      return verifyPomFailed('The file does not have valid XML syntax.');
    }
    var attrs = {};
    for (var i = 0, attr_name; attr_name = PomAttrs[i]; i++) {
      attrs[attr_name] = doc.find('project > ' + attr_name).text();
    } 
    attrs.hasParent = doc.find('project > parent').length > 0;
    return attrs;
  }

  /*
  Utility function for retrieving the first element in an array, or null if array is empty.
  */
  function firstInArray(arr) {
    for (var i = 0, elem; elem = arr[i]; i++) {
      if (typeof arr[i] !== 'undefined' && arr[i] !== null)
        return elem;
    }
    return null;
  }

  /*
  Has the pom file been successfully verified?
  True only if the user has selected a valid pom file.
  False if the user has not selected a file or a valid pom file.
  */
  var pomVerified = false;

  /*
  Sets the UI to show that the pom is valid.
  */
  function verifyPomOk() {
    $('#pom-verifying').hide();
    $('#pom-info').show();
    $('#pom-verify-status').append('<div class="label label-success">Pom is valid</div>');
    pomVerified = true;
    updateSubmitState();
  }

  /*
  Sets the UI to show that the pom is invalid.
  */
  function verifyPomFailed(msg) {
    $('#pom-verifying').hide();
    $('#pom-verify-status').append('<div class="label label-important">Pom is not valid</div>');
    addStatusMsg('error', msg);
    pomVerified = false;
    updateSubmitState();
    return null;
  }

  /*
  Resets the UI to its original state.
  */
  function resetPomVerify() {
    $('#pom-status-msgs').text('');
    $('#pom-verify-status').text('');
    $('#pom-info').hide();
    $('#pom-advice li').removeClass('text-error').removeClass('text-warning');
    pomVerified = false;
    updateSubmitState();
  }

  /*
  Tests if an artifact exists in the Maven app repository.
  Parameters:
    - attrs: the object returned by extractPomAttrs. i.e. {'groupId': ..., 'artifactId': ..., ...}
    - callback: a function that takes a single boolean argument -- true if artifact exists, false otherwise
  */
  function doesArtifactExist(attrs, callback) {
    $.post('/submit_app/artifact_exists', attrs, callback);
  }

  /*
  Checks pom xml file to ensure that the project coordinates are ok.
  */
  function verifyPom(attrs) {
    /* Does the pom xml file have each coordinate? */
    for (var i = 0, attr_name; attr_name = PomAttrs[i]; i++) {
      var attr = attrs[attr_name];
      if (attr.length === 0) {
        $('#pom-advice-coordinates').addClass('text-error');
        return verifyPomFailed('No <tt>' + attr_name + '</tt> tag found under the <tt>project</tt> tag.');
      }
      $('#pom-info-' + attr_name + ' > td:first-child+td').text(attr);
    }

    /* Disallow group IDs that begin with org.cytoscape */
    if (attrs.groupId === 'org.cytoscape' || attrs.groupId.indexOf('org.cytoscape.') === 0) {
      $('#pom-advice-no-cyto').addClass('text-error');
      return verifyPomFailed('The group ID cannot begin with <tt>org.cytoscape</tt>.');
    }

    /* Issue warning if parent tag exists */
    if (attrs.hasParent) {
      $('#pom-advice-parent').addClass('text-warning');
      addStatusMsg('warning', 'This pom file references a parent. Make sure dependencies are restated in your pom file so that others can compile against it.');
    }

    /* Check to see if artifact already exists in the Maven app repository */
    doesArtifactExist(attrs, function(artifactExists) {
      if (artifactExists) {
        $('#pom-advice-no-replacing').addClass('text-error');
        return verifyPomFailed('A release already exists with the same group, artifact, and version. Try changing the version.');
      } else {
        return verifyPomOk();
      }
    });
  }

  /* Updates the submit button's enabled state */
  function updateSubmitState() {
    var canSubmit = pomVerified && ($('input[name=javadocs_jar]').val());
    if (canSubmit) {
      $('button[name=submit]').removeAttr('disabled');
    } else {
      $('button[name=submit]').attr('disabled', 'true');
    }
  }

  /* Set up both the pom_xml and javadocs_jar file fields */
  function setupInputFiles() {
    /* set up pom_xml field */
    $('input[name=pom_xml]').click(function(e) {
      $(this).val(null); // allows reselecting the same file again
      resetPomVerify();
    }).change(function(e) {
      var file = firstInArray(e.target.files);
      if (file === null)
        return;

      $('#pom-verifying').show();

      if (file.type !== 'text/xml') {
        return verifyFailed(file.name + " is not an XML file");
      }

      var reader = new FileReader();
      reader.onload = function(e) {
        attrs = extractPomAttrs(e.target.result);
        if (attrs === null)
          return;
        verifyPom(attrs);
      };

      reader.readAsText(file);
    });

    /* set up javadocs_jar field */
    $('input[name=javadocs_jar]').click(function(e) {
      $(this).val(null);
      updateSubmitState();
    }).change(function(e) {
      updateSubmitState();
    });
  }
 
  return {
    'setupInputFiles': setupInputFiles,
  };
})($);