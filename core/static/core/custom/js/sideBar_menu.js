(function($) {
  "use strict"; // Start of use strict

  // Toggle the side navigation
  $("#sidebarToggle, #sidebarToggleTop").on('click', function(e) {
    $("body").toggleClass("sidebar-toggled");
    $(".sidebar").toggleClass("toggled");
  
    if ($(".sidebar").hasClass("toggled")) {
      $('.sidebar .collapse').collapse('hide');
    }
  
    // Change arrow icon
    const $icon = $(this).find("i.toggle-icon");
    $icon.toggleClass("bi-chevron-left bi-chevron-right");
  });

// Auto-collapse sidebar on small screens
function autoCollapseSidebar() {
  if ($(window).width() < 768) {
    $("body").addClass("sidebar-toggled");
    $(".sidebar").addClass("toggled");
    $('.sidebar .collapse').collapse('hide');

    $("#sidebarToggle").find("i.toggle-icon")
      .removeClass("bi-chevron-left")
      .addClass("bi-chevron-right");
  } else {
    $("body").removeClass("sidebar-toggled");
    $(".sidebar").removeClass("toggled");
    $("#sidebarToggle").find("i.toggle-icon")
      .removeClass("bi-chevron-right")
      .addClass("bi-chevron-left");
  }
}

$(document).ready(function() {
  autoCollapseSidebar();
});

$(window).resize(function() {
  autoCollapseSidebar();
});

  // Prevent the content wrapper from scrolling when the fixed side navigation hovered over
  $('body.fixed-nav .sidebar').on('mousewheel DOMMouseScroll wheel', function(e) {
    if ($(window).width() > 768) {
      var e0 = e.originalEvent,
        delta = e0.wheelDelta || -e0.detail;
      this.scrollTop += (delta < 0 ? 1 : -1) * 30;
      e.preventDefault();
    }
  });

  // Scroll to top button appear
  $(document).on('scroll', function() {
    var scrollDistance = $(this).scrollTop();
    if (scrollDistance > 100) {
      $('.scroll-to-top').fadeIn();
    } else {
      $('.scroll-to-top').fadeOut();
    }
  });

  // Smooth scrolling using jQuery easing
  $(document).on('click', 'a.scroll-to-top', function(e) {
    var $anchor = $(this);
    $('html, body').stop().animate({
      scrollTop: ($($anchor.attr('href')).offset().top)
    }, 1000, 'easeInOutExpo');
    e.preventDefault();
  });
})(jQuery); // End of use strict
