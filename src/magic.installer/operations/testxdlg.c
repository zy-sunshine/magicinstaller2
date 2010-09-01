/* Copyright (C) 2003, Charles Wang.
 * Author:  Charles Wang <charles@linux.net.cn>
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation; either version 2, or (at your option) any later
 * version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANT; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public LIcense for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, 59 Temple
 * Place - Suite 330, Boston, MA 02111-1307, USA.
 */
#include  <libintl.h>
#include  <locale.h>
#include  <stdio.h>
#include  <unistd.h>
#include  <gdk/gdk.h>
#include  <gtk/gtk.h>

#define   _(x)  gettext(x)
#define   N_(x) (x)

#define   TIMEOUT_MAX   10

#define   DOMAIN        "testxdlg"
#define   POSITION      "/tmp/testxdlg"

static const char *btnfmt = N_("_OK - %02d");

GtkWidget *button;
gboolean  timeout_func(gpointer  data) {
    int  *pto_cnt;
    char  btntextbuf[32];

    pto_cnt = (int *)data;
    (*pto_cnt)--;

    snprintf(btntextbuf, sizeof(btntextbuf), _(btnfmt), *pto_cnt);
    gtk_button_set_label(GTK_BUTTON(button), btntextbuf);

    if (*pto_cnt) return TRUE;

    gtk_main_quit();

    return  FALSE;
}

void ok_clicked(GtkButton *button, gpointer data) {
    unlink(POSITION "/probe_x_mark");
    printf("OK clicked.\n");
    gtk_main_quit();
}

void cancel_clicked(GtkButton *button, gpointer data) {
    gtk_main_quit();
}

int main(int argc, char *argv[]) {
    GtkWidget  *window;
    GtkWidget  *frame0;
    GtkWidget  *frame1;
    GtkWidget  *vbox;
    GtkWidget  *hbox;
    GtkWidget  *label;
    GtkWidget  *cancelbutton;

    GtkWidget  *image;
    GdkWindow  *root;
    GdkCursor  *cursor;
    GdkPixbuf  *bkpixbuf;
    GdkPixmap  *bkpixmap;

    int         timeout_cnt;
    char        btntextbuf[32];

    gtk_init(&argc, &argv);

    bindtextdomain(DOMAIN, POSITION);
    bind_textdomain_codeset(DOMAIN, "UTF-8");
    textdomain(DOMAIN);

    window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_position(GTK_WINDOW(window), GTK_WIN_POS_CENTER);

    frame0 = gtk_frame_new(NULL);
    gtk_frame_set_shadow_type(GTK_FRAME(frame0), GTK_SHADOW_OUT);
    gtk_container_add(GTK_CONTAINER(window), frame0);

    frame1 = gtk_frame_new(NULL);
    gtk_frame_set_shadow_type(GTK_FRAME(frame1), GTK_SHADOW_IN);
    gtk_container_add(GTK_CONTAINER(frame0), frame1);

    vbox = gtk_vbox_new(FALSE, 4);
    gtk_container_set_border_width(GTK_CONTAINER(vbox), 4);
    gtk_container_add(GTK_CONTAINER(frame1), vbox);

    label = gtk_label_new(_("Please click 'OK' before timeout if you can see it."));
    gtk_box_pack_start(GTK_BOX(vbox), label, TRUE, TRUE, 0);

    hbox = gtk_hbox_new(FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), hbox, FALSE, FALSE, 0);

    label = gtk_label_new("");
    gtk_box_pack_start(GTK_BOX(hbox), label, TRUE, FALSE, 0);

    timeout_cnt = TIMEOUT_MAX;
    snprintf(btntextbuf, sizeof(btntextbuf), _(btnfmt), timeout_cnt);
    button = gtk_button_new_with_mnemonic(btntextbuf);
    g_signal_connect(G_OBJECT(button), "clicked",
		     G_CALLBACK(ok_clicked), NULL);
    gtk_box_pack_start(GTK_BOX(hbox), button, FALSE, FALSE, 0);

    label = gtk_label_new("");
    gtk_box_pack_start(GTK_BOX(hbox), label, TRUE, FALSE, 0);

    cancelbutton = gtk_button_new_with_mnemonic(_("_Cancel"));
    g_signal_connect(G_OBJECT(cancelbutton), "clicked",
		     G_CALLBACK(cancel_clicked), NULL);
    gtk_box_pack_start(GTK_BOX(hbox), cancelbutton, FALSE, FALSE, 0);

    label = gtk_label_new("");
    gtk_box_pack_start(GTK_BOX(hbox), label, TRUE, FALSE, 0);

    root = gdk_get_default_root_window();

    cursor = gdk_cursor_new(GDK_LEFT_PTR);
    gdk_window_set_cursor(root, cursor);

    image = gtk_image_new_from_file(POSITION "/txbackground.png");
    bkpixbuf = gtk_image_get_pixbuf(GTK_IMAGE(image));
    gdk_pixbuf_render_pixmap_and_mask(bkpixbuf, &bkpixmap, NULL, 0);
    gdk_window_set_back_pixmap(root, bkpixmap, 0);
    gdk_window_clear(root);

    gtk_widget_show_all(window);

    gtk_timeout_add(1000, timeout_func, &timeout_cnt);

    gtk_main();

    return 0;
}
