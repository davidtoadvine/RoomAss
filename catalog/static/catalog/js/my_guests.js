$(document).ready(function() {
    
  // Populate the extend and shorten modals with the event data
  $('.modal').on('show.bs.modal', function(event) {
    var button = $(event.relatedTarget);
    var startDate = button.data('original-start');
    var endDate = button.data('original-end');
    var eventId = button.data('id');
    var modal = $(this);


    // Store the eventId in the modal's data attribute
    modal.data('event-id', eventId);

    // For Extend Modal
    modal.find(`#extend-booking-start-date`).val(startDate).attr('data-original-start', startDate);
    modal.find(`#extend-booking-end-date`).val(endDate).attr('data-original-end', endDate);

    // For Shorten Modal
    modal.find(`#shorten-booking-start-date`).val(startDate).attr('data-original-start', startDate);
    modal.find(`#shorten-booking-end-date`).val(endDate).attr('data-original-end', endDate);

    // Set the event_id field value explicitly
    modal.find(`#extend-booking-event-id`).val(eventId);
    modal.find(`#shorten-booking-event-id`).val(eventId);

    modal.find(`#delete-booking-event-id`).val(eventId);
  });
  $('#extend-booking-modal').on('show.bs.modal', function(event) {
    var button = $(event.relatedTarget);
    //var sectionId = "{{ section_id|default:'' }}";
    var eventId = button.data('id');
    var modal = $(this);
    // Update the form action URL
    let formAction = '';
    if (sectionId) {
      formAction = `/catalog/extend_booking/${eventId}/${sectionId}/`;
    } else {
      formAction = `/catalog/extend_booking/${eventId}/`;
    }
    modal.find('#extend-booking-form').attr('action', formAction);
  });
  $('#shorten-booking-modal').on('show.bs.modal', function(event) {
    var button = $(event.relatedTarget);
    //var sectionId = "{{ section_id|default:'' }}";
    var eventId = button.data('id');
    var modal = $(this);
    // Update the form action URL
    let formAction = '';
    if (sectionId) {
      formAction = `/catalog/shorten_booking/${eventId}/${sectionId}/`;
    } else {
      formAction = `/catalog/shorten_booking/${eventId}/`;
    }
    modal.find('#shorten-booking-form').attr('action', formAction);
  });
  $('#delete-booking-modal').on('show.bs.modal', function(event) {
    var button = $(event.relatedTarget);
    //var sectionId = "{{ section_id|default:'' }}";
    var eventId = button.data('id');
    var modal = $(this);
    // Update the form action URL
    let formAction = '';
    if (sectionId) {
      formAction = `/catalog/delete_booking/${eventId}/${sectionId}/`;
    } else {
      formAction = `/catalog/delete_booking/${eventId}/`;
    }
    modal.find('#delete-booking-form').attr('action', formAction);
  });
  
 // Add the validation functions here (validateExtendDate and validateShortenDate)...
  // Function to validate date selection
  function validateExtendDate(eventId) {
    console.log(`Validating extend date for event ${eventId}`);
    let startDateInput = document.getElementById(`extend-booking-start-date`);
    let endDateInput = document.getElementById(`extend-booking-end-date`);
    let originalStartDate = new Date(startDateInput.getAttribute('data-original-start'));
    let originalEndDate = new Date(endDateInput.getAttribute('data-original-end'));
    let newStartDate = new Date(startDateInput.value);
    let newEndDate = new Date(endDateInput.value);
  
    if (newStartDate > originalStartDate || newEndDate < originalEndDate) {
      alert("New dates cannot shrink the original reservation window. Please use the 'Shorten' button for that.");
      startDateInput.value = startDateInput.getAttribute('data-original-start');
      endDateInput.value = endDateInput.getAttribute('data-original-end');
      return false;
    }
    return true;
  }
  
  
  
  function validateShortenDate(eventId) {
    console.log(eventId)
    console.log(`Validating shorten date for event ${eventId}`);
    let startDateInput = document.getElementById(`shorten-booking-start-date`);
    let endDateInput = document.getElementById(`shorten-booking-end-date`);
    let originalStartDate = new Date(startDateInput.getAttribute('data-original-start'));
    let originalEndDate = new Date(endDateInput.getAttribute('data-original-end'));
    let newStartDate = new Date(startDateInput.value);
    let newEndDate = new Date(endDateInput.value);
  
    if (newStartDate < originalStartDate || newEndDate > originalEndDate) {
      alert("New dates cannot extend the original reservation window. Please use the 'Extend' button for that.");
      startDateInput.value = startDateInput.getAttribute('data-original-start');
      endDateInput.value = endDateInput.getAttribute('data-original-end');
      return false;
    }
    else if (newStartDate >= originalEndDate || newEndDate <= originalStartDate){
      alert("The start date cannot occur on or after the end date. If you wish to delete this event, please use the 'Delete' button.");
      startDateInput.value = startDateInput.getAttribute('data-original-start');
      endDateInput.value = endDateInput.getAttribute('data-original-end');
      return false;
    }
    return true;
  } 
  // Attach change event listeners to the date inputs
$(document).on('change', '.shorten-booking-start-date, .shorten-booking-end-date', function() {
  const eventId = $(this).closest('.modal').find('input[name="event_id"]').val();
  console.log(eventId)
  validateShortenDate(eventId);
});
// Attach change event listeners to the date inputs
$(document).on('change', '.extend-booking-start-date, .extend-booking-end-date', function() {
  const eventId = $(this).closest('.modal').find('input[name="event_id"]').val();
  console.log(eventId)
  validateExtendDate(eventId);
});





  // Prevent form submission if validation fails
  $(document).on('submit', 'form[data-form-type]', function(e) {
    e.preventDefault(); // Prevent the default form submission
    const form = $(this);
    const eventId = form.find('input[name="event_id"]').val();
    const formType = form.attr('data-form-type');

    if ((formType === 'extend' && validateExtendDate(eventId)) || 
      (formType === 'shorten' && validateShortenDate(eventId)) || 
      formType === 'delete') { // No validation for delete, just submit
    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function(response) {
          if (response.status === 'success') {
            if (response.redirect_url) {
              window.location.href = response.redirect_url; // Redirect to the URL provided in the response
            } else {
              // Handle the case where no redirect URL is provided (update the modal or page content as needed)
              alert('Booking updated successfully');
            }
          } else if (response.status === 'error') {
            displayFormErrors(form, response.errors);
          } else if (response.status === 'conflict') {
            // Handle conflict response if necessary
            alert('There is a conflict with the new dates.');
          }
        },
        error: function(xhr, status, error) {
          console.error('Error:', error);
          alert('An error occurred while processing your request. Please try again.');
        }
      });
    }
  });

  


});

// Function to submit extend form
function submitExtendBookingForm() {
  console.log('SUBMIT EXTEND BOOKING FORM')
  var form = $(`#extend-booking-form`);
  console.log(form)
  var formData = form.serialize();
  console.log(formData)

  $.ajax({
    type: "POST",
    url: form.attr('action'),
    data: formData,
    success: function(response) {
      if (response.status === 'success') {
        // Redirect to the appropriate URL
        window.location.href = response.redirect_url;
      } else if (response.status === 'error') {
        // Display errors in the modal
        displayFormErrors(form, response.errors);
      } else if (response.status === 'conflict') {
        // Handle conflict
        alert(`Conflict detected: Start - ${response.start}, End - ${response.end}`);
      }
    },
    error: function(xhr, status, error) {
      // Handle the error
      console.error("An error occurred:", status, error);
      alert("An error occurred while submitting the form. Please try again.");
    }
  });
}

// Function to submit shorten form
function submitShortenBookingForm() {
  var form = $(`#shorten-booking-form`);
  var formData = form.serialize();
  var csrfToken = form.find('[name="csrfmiddlewaretoken"]').val();
  console.log("CSRF Token:", csrfToken);

  $.ajax({
    type: "POST",
    url: form.attr('action'),
    data: formData,
    success: function(response) {
      if (response.status === 'success') {
        // Redirect to the appropriate URL
        window.location.href = response.redirect_url;
      } else if (response.status === 'error') {
        // Display errors in the modal
        displayFormErrors(form, response.errors);
      } else if (response.status === 'conflict') {
        // Handle conflict
        alert(`Conflict detected: Start - ${response.start}, End - ${response.end}`);
      }
    },
    error: function(xhr, status, error) {
      // Handle the error
      console.error("An error occurred:", status, error);
      alert("An error occurred while submitting the form. Please try again.");
    }
  });
}

// Function to submit delete form
function submitDeleteBookingForm() {
  console.log("SUBMITTING DELETE FORM")
  var form = $(`#delete-booking-form`);
  console.log(form)
  var csrfTokenInput = form.find('input[name="csrfmiddlewaretoken"]');
  var csrfToken = csrfTokenInput.val();

  // Debugging logs
  console.log('Form:', form);
  console.log('CSRF Token Input:', csrfTokenInput);
  console.log('CSRF Token:', csrfToken);

  //var sourcePage= form.find('input[name="source_page"]').val();
  //console.log(sourcePage);

  if (!csrfToken) {
    alert("CSRF token not found!");
    return;
  }

  var formData = form.serialize();

  
  $.ajax({
    type: "POST",
    url: form.attr('action'),
    data: formData,
    success: function(response) {
      if (response.status === 'success') {
        // Redirect to the appropriate URL
        window.location.href = response.redirect_url;
      } else if (response.status === 'error') {
        // Display errors in the modal
        displayFormErrors(form, response.errors);
      } 
    },
    error: function(xhr, status, error) {
      // Handle the error
      console.error("An error occurred:", status, error);
      alert("An error occurred while submitting the form. Please try again.");
    }
  });
}

// Display form errors in the modal
function displayFormErrors(form, errors) {
  // Clear previous errors
  form.find('.form-error').remove();

  // Display new errors
  $.each(errors, function(field, messages) {
    const input = form.find(`[name="${field}"]`);
    if (input.length) {
      const errorHtml = `<div class="form-error text-danger">${messages.join('<br>')}</div>`;
      input.after(errorHtml);
    }
  });
}

// Function to show the floorplan modal with the correct image
function showFloorplanModal(imageUrl, roomName) {
  document.getElementById('floorplan-image').src = imageUrl;
  document.getElementById('floorplan-modal-label').innerText = roomName;
  console.log("roomname" + roomName)
  $('#floorplan-modal').modal('show');
}