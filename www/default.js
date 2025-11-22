
document.addEventListener("DOMContentLoaded", function () {
  initChannelStates();
  initChannelPwrStates()
});

window.onblur = function(){window.onfocus = function(){location.reload(true)}};

function enablechannelpwr() {
  fetch("/api/set_relay_pwr", {
          method: "POST",
          body: JSON.stringify({value: 1}),
          headers: {
              "Content-Type": "application/json;"
          }
  }).then(response => {
    if (response.status != 200) {
      throw new Error(response.status);
    }
    document.getElementById("button_enable_relay_pwr").disabled = true
    document.getElementById("button_disable_relay_pwr").disabled = false
    document.getElementById("label_relay_pwr_status").innerHTML = "<span style='color: red; font-weight: bold'>ON</span>"
  }).catch(error => console.error(error));
}

function disablechannelpwr() {
  fetch("/api/set_relay_pwr", {
          method: "POST",
          body: JSON.stringify({value: 0}),
          headers: {
              "Content-Type": "application/json;"
          }
  }).then(response => {
    if (response.status != 200) {
      throw new Error(response.status);
    }
    document.getElementById("button_enable_relay_pwr").disabled = false
    document.getElementById("button_disable_relay_pwr").disabled = true
    document.getElementById("label_relay_pwr_status").innerHTML = "<span style='color: green; font-weight: bold'>off</span>"
  }).catch(error => console.error(error));
}

function initChannelPwrStates() {
  fetch("/api/get_relay_pwr", {
      method: "GET"
  }).then(response => {
    if (response.status >= 200 && response.status < 300) {
      return response.json();
    } else {
      console.error(response.statusText);
    }
  }).then(data => {
    // data = { value: 0/1 }
    data.forEach(value =>{
      if (value.value === 1) {
        document.getElementById("button_enable_relay_pwr").disabled = true
        document.getElementById("button_disable_relay_pwr").disabled = false
        document.getElementById("label_relay_pwr_status").innerHTML = "<span style='color: red; font-weight: bold;'>ON</span>"
      } else if (value.value === 0) {
        document.getElementById("button_enable_relay_pwr").disabled = false
        document.getElementById("button_disable_relay_pwr").disabled = true
        document.getElementById("label_relay_pwr_status").innerHTML = "<span style='color: green; font-weight: bold'>off</span>"
      }
    })
  }).catch(error => console.error(error));
}

function initChannelStates() {
  fetch("/api/get_channel_states", {
      method: "GET"
  }).then(response => {
    if (response.status >= 200 && response.status < 300) {
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
  }).catch(error => console.error(error));
}

function set_channel(params) {
  fetch("/api/set_channel_states", {
    method: "POST",
    body: JSON.stringify({
      params
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
  }).catch(error => console.error(error));
}