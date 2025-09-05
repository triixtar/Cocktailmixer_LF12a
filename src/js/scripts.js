let drinkBtn = document.getElementsByClassName("drink-button")
console.log(drinkBtn)
drinkBtn[0].addEventListener("click", function() {
console.log(this.innerHTML)

})
function openPopup() {
    let test = document.getElementById("bgLayer")
        test.classList.add('active')
    console.log(test.classList)

}

function closePopup() {
    document.getElementById("bgLayer").classList.remove('active')
}
