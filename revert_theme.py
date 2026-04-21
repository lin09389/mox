import os
import glob
import re

def reverse_theme(directory):
    replacements = [
        # Restore basic colors
        ('bg-graphite-950', 'bg-white'),
        ('text-neon-400', 'text-graphite-950'),
        ('text-graphite-100', 'text-graphite-900'),
        ('text-graphite-200', 'text-graphite-800'),
        ('text-graphite-300', 'text-graphite-700'),
        ('text-graphite-400', 'text-graphite-600'),
        
        # Restore borders
        ('border-neon-500/20', 'border-white'),
        ('border-neon-500/30', 'border-white/30'),
        ('border-neon-500/40', 'border-white/40'),
        ('border-neon-500/50', 'border-white/50'),
        ('border-neon-500/60', 'border-white/60'),
        ('border-neon-500/70', 'border-white/70'),
        ('border-neon-500/80', 'border-white/80'),
        ('border-neon-500/90', 'border-white/90'),
        ('border-graphite-800', 'border-graphite-200'),
        
        # Restore backgrounds
        ('bg-graphite-900', 'bg-graphite-50'),
        ('bg-graphite-800', 'bg-graphite-100'),
        ('hover:bg-graphite-800', 'hover:bg-graphite-50'),
        ('hover:bg-graphite-900', 'hover:bg-white'),
        
        # Restore colored backgrounds
        ('bg-electric-900/30', 'bg-electric-50'),
        ('bg-amber-900/30', 'bg-amber-50'),
        ('bg-lava-900/30', 'bg-lava-50'),
        ('bg-neon-900/30', 'bg-neon-50'),
        
        # Restore shadows
        ('shadow-glow-neon', 'shadow-soft'),
        ('shadow-[0_0_10px_rgba(34,197,94,0.1)]', 'shadow-sm'),
        
        # Restore specific texts
        ('text-electric-400', 'text-electric-700'),
        ('border-neon-500', 'border-white'),
    ]

    for filepath in glob.glob(os.path.join(directory, '**', '*.jsx'), recursive=True) + glob.glob(os.path.join(directory, '**', '*.js'), recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)
            
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Reverted {filepath}")

reverse_theme('c:/Users/JHJ/Desktop/mox/frontend/src')
