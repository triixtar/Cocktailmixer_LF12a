let drinkBtn = document.getElementsByClassName("drink-button")
console.log(drinkBtn)
drinkBtn[0].addEventListener("click", function() {
console.log(this.innerHTML)

})
function openPopup() {
    document.getElementById("bgLayer").classList.add('active')
}

function closePopup() {
    document.getElementById("bgLayer").classList.remove('active')
}
