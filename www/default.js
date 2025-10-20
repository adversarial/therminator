
document.addEventListener("DOMContentLoaded", function () {
  initChannelStates();
});

function initChannelStates() {
  fetch("/api/get_channel_states", {
      method: "GET"
  }).then(response => {
    if (response.status === 200) {
      return response.json();
    } else {
      console.error(response.statusText);
    }
  }).then(data => {
    data.forEach(channel =>{
      let enabled_button_id = "button_channel" + String(channel.channel);
      let alternate_button_id = enabled_button_id
      if (channel.enable === 1) {
        enabled_button_id += "_disable"
      } else {
        alternate_button_id += "_disable"
      }
      document.getElementById(enabled_button_id).disabled = false;
      document.getElementById(alternate_button_id).disabled = true;
    })
  })
  .catch(error => console.error(error));
}

function set_channel(params) {
  fetch("/api/set_channel_states", {
    method: "POST",
    body: JSON.stringify({
      params
      /*
      channel: params.channel,
      enable: params.enable
    */
    }),
    headers: {
      "Content-Type": "application/json;"
    }
  }).then(response => {
    if (response.status === 200) {
      params.forEach(param => {
        let pressed_button_id = "button_channel" + String(param.channel);
        let alternate_button_id = pressed_button_id;
        if (param.enable === 0) {
          pressed_button_id += "_disable";
        } else {
          alternate_button_id += "_disable";
        }
        document.getElementById(pressed_button_id).disabled = true;
        document.getElementById(alternate_button_id).disabled = false;
        })
    }
  }).catch(function(error) {
    console.error(error)
  });
}