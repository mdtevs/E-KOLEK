
  document.getElementById('downloadBtn').onclick = async function() {
    const cards = document.querySelectorAll('.id-card, .id-card-back');
    for (let i = 0; i < cards.length; i++) {
      const card = cards[i];
      // Temporarily set background to white for better PNG
      const prevBg = card.style.backgroundColor;
      card.style.backgroundColor = "#fff";
      await html2canvas(card, {useCORS: true, scale: 2}).then(canvas => {
        const link = document.createElement('a');
        link.download = `idcard_${i % 2 === 0 ? 'front' : 'back'}_${Math.floor(i/2)+1}.png`;
        link.href = canvas.toDataURL();
        link.click();
      });
      card.style.backgroundColor = prevBg;
    }
  };
