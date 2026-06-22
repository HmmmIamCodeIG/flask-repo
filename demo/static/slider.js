const slider = document.getElementById("myRange");
const output = document.getElementById("demo");

if (slider && output) {
  output.innerHTML = slider.value;

  slider.oninput = function() {
    output.innerHTML = this.value;
  };
}