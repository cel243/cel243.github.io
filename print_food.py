
import os
import re
import sys

OUT_FILE = f"index.html"
DIRNAME = "FoodView Photos"

def to_am_pm_time(time_str):
  hr = time_str[:2]
  m = time_str[3:]
  txt = "AM"
  if int(hr) == 12:
    txt = "PM"
  if int(hr) > 12:
    hr = int(hr) - 12
    txt = "PM"
  return f"{int(hr)}:{m} {txt}"

def get_header(size, text, styling=""):
  return f"    <h{size} {styling}>{text}</h{size}>\n"

def get_img_html(src_ls):
  img_html_ls = []
  for src in src_ls:
    img_html_ls.append(f"      <img class=\"img-class\" src=\"{src}\"/>\n")
  return ["<div class=\"img-container\">"] + img_html_ls + ["</div>"]

def get_time_html(figure_times):
  if len(figure_times) < 2:
    return get_header("2", figure_times[0])
  else:
    return get_header("2", f"{figure_times[0]} - {figure_times[-1]}")

def get_grouping_id(note):
  id_search = re.search(".*:([0-9]+):", note)
  if not id_search:
    id_search = re.search(".*\[([0-9]+)\]", note)
  if id_search:
    return id_search.group(1)
  else:
    return None

# Returns the text of the image caption, if it exists, along with
# other stuff. The full output:
# new index in filenames (might be the same),
# Then a tuple that contains:
# caption, group id, is binge, is note only
def get_text_caption(filenames, i):
  if i == len(filenames) - 1:
    return i, None
  filename = filenames[i+1]
  if re.match(".*.jpg$", filename):
    return i, None
  else:
    with open(os.path.join(DIRNAME, filename), 'r') as f:
      note = f.read().strip()
      group_id = get_grouping_id(note)
      is_binge = True if (re.search(".*:binge:", note, re.IGNORECASE) is not None) or (re.search(".*\[binge\]", note, re.IGNORECASE) is not None) else None
      is_note_only = True if (re.search(".*:note:", note, re.IGNORECASE) is not None) or (re.search(".*\[note\]", note, re.IGNORECASE) is not None) else None
      caption = re.sub(":[^:]+:", "", note).strip()
      caption = re.sub("\[[^\[\]]+\]", "", caption).strip()
      return i+1, (caption, group_id, is_binge, is_note_only)

# return figure_info (possibly updated), new_figure_info (possibly None)
def get_figure_info(caption_info_tuple, figure_info, img_time, img_source):
  if not caption_info_tuple:
    new_figure_info = {
      "times" : [img_time],
      "images" : [img_source],
      "caption_lines" : [],
      "group_id" : None,
      "note_only" : False,
      "binge" : False
    }
    return figure_info, new_figure_info
  if caption_info_tuple:
    caption, group_id, is_binge, is_note_only = caption_info_tuple
    if group_id and figure_info and group_id == figure_info["group_id"]:
      figure_info["times"].append(img_time)
      figure_info["images"].append(img_source)
      if caption:
        figure_info["caption_lines"].append(caption)
      figure_info["binge"] = figure_info["binge"] or is_binge
      return figure_info, None
    else:
      new_figure_info = {
        "times" : [img_time],
        "images" : [img_source],
        "caption_lines" : [caption] if caption else [],
        "group_id" : group_id,
        "note_only" : is_note_only,
        "binge" : is_binge
      }
      return figure_info, new_figure_info

def add_figure_to_output(figure_info, out_lines):
  if not figure_info:
    return out_lines
  binge_class = "binge" if figure_info["binge"] else ""
  caption = "<br>".join(figure_info["caption_lines"])
  image_html_ls = [""] if figure_info["note_only"] else get_img_html(figure_info["images"])
  return out_lines + (
    [f"   <figure class=\"inner-figure {binge_class}\">\n",
            get_time_html(figure_info["times"])] +
            image_html_ls + [
    f"      <figcaption>{caption}</figcaption>\n",
     "    </figure>\n"])


out_lines = []
nav_tabs = "<div class=\"tab\">"

filenames = os.listdir(DIRNAME)
filenames.sort() 
date = None
image_id = None
figure_info = None
i = 0
while i < len(filenames):
  filename = filenames[i]
  if not re.search("^\d{4}", filename):
    i += 1
    continue
  # if DATE is not None:
  #   if not re.search(f"^{DATE}", filename):
  #     i += 1
  #     continue

  if re.match(".*.jpg$", filename):
    img_time = to_am_pm_time(re.search("T(\d{2}-\d{2})", filename).group(1).replace("-", ":"))
    img_source = f"{DIRNAME}/{filename}"
    i, caption_info_tuple = get_text_caption(filenames, i)
    figure_info, new_figure_info = get_figure_info(caption_info_tuple, figure_info, img_time, img_source)
    if new_figure_info:
      # Should print the old figure info if we found a new figure!
      out_lines = add_figure_to_output(figure_info, out_lines)
      figure_info = new_figure_info

  date_from_filename = re.search("^(\d{4}-\d{2}-\d{2})", filename).group(1)
  if date_from_filename != date:
    date = date_from_filename
    out_lines.append(f"    </div><div id=\"{date}\" class=\"tabcontent\"><h1>{date}</h1>\n")
    nav_tabs += f"<button class=\"tablinks\" onclick=\"openDate(event, '{date}')\">{date}</button>"

  i += 1

out_lines = add_figure_to_output(figure_info, out_lines)

out_lines = [
"<!doctype html>\n",
"<html lang=\"en\">\n",
"  <head>\n",
"    <link href=\"css/styles.css\" rel=\"stylesheet\" />\n",
"  </head> <body> \n",
f"{nav_tabs}</div>\n",
"  <div>\n"
] + out_lines + [
  "  </div><script src=\"js/scripts.js\"></script>\n",
  "  </body>\n",
"</html>\n"
]
with open(OUT_FILE, 'w') as f:
  f.writelines(out_lines)
