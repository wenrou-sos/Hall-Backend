from PIL import Image, ImageDraw, ImageFont
import textwrap

def draw_multiple_line_text(image, text, font, text_color, text_start_height):
    '''
    From unutbu on [python PIL draw multiline text on image](https://stackoverflow.com/a/7698300/395857)
    '''
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=20)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text),
                  line, font=font, fill=text_color)
        y_text += line_height


def main():
    '''
    Testing draw_multiple_line_text
    '''
    #image_width
    image = Image.new('RGB', (800, 600), color = (255, 255,255))
    fontsize = 40  # starting font size
    font = ImageFont.truetype("font-chinese.otf", fontsize)
    text1 = "這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字這裡最多打八個字"

    text_color = (0, 0, 0)
    text_start_height = 0
    draw_multiple_line_text(image, text1, font, text_color, text_start_height)
    # draw_multiple_line_text(image, text2, font, text_color, 400)
    image.save('pil_text.png')

if __name__ == "__main__":
    main()